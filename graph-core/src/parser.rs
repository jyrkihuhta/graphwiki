//! Markdown parser for wiki link and frontmatter extraction.
//!
//! This module provides functions to parse markdown files and extract:
//! - YAML frontmatter (metadata between `---` markers)
//! - Wiki links (`[[PageName]]` and `[[PageName|Display Text]]` syntax)

use crate::models::ParsedLink;
use std::collections::HashMap;

/// Result of parsing a markdown file.
#[derive(Clone, Debug, Default)]
pub struct ParsedPage {
    /// Extracted frontmatter metadata
    pub metadata: HashMap<String, Vec<String>>,

    /// Wiki links found in the content
    pub links: Vec<ParsedLink>,

    /// The content without frontmatter (markdown body)
    pub content: String,
}

/// Parse YAML frontmatter from markdown content.
///
/// Frontmatter is expected to be at the very beginning of the file,
/// enclosed between two `---` lines.
///
/// # Example
/// ```text
/// ---
/// status: draft
/// tags:
///   - rust
///   - wiki
/// ---
/// # Page Content
/// ```
///
/// Returns the parsed metadata as a HashMap where values are always Vec<String>
/// to support both single values and lists.
pub fn parse_frontmatter(content: &str) -> HashMap<String, Vec<String>> {
    let mut metadata = HashMap::new();

    // Check if content starts with frontmatter delimiter
    let trimmed = content.trim_start();
    if !trimmed.starts_with("---") {
        return metadata;
    }

    // Find the closing delimiter
    let after_first = &trimmed[3..];
    let end_pos = after_first.find("\n---");

    if let Some(pos) = end_pos {
        let yaml_content = &after_first[..pos].trim();

        // Parse the YAML
        if let Ok(yaml_value) = serde_yaml::from_str::<serde_yaml::Value>(yaml_content) {
            if let serde_yaml::Value::Mapping(map) = yaml_value {
                for (key, value) in map {
                    if let serde_yaml::Value::String(key_str) = key {
                        let values = yaml_value_to_strings(&value);
                        if !values.is_empty() {
                            metadata.insert(key_str, values);
                        }
                    }
                }
            }
        }
    }

    metadata
}

/// Convert a YAML value to a Vec<String>.
///
/// - Strings become single-element vectors
/// - Arrays of strings become multi-element vectors
/// - Numbers, booleans, etc. are converted to their string representation
fn yaml_value_to_strings(value: &serde_yaml::Value) -> Vec<String> {
    match value {
        serde_yaml::Value::String(s) => vec![s.clone()],
        serde_yaml::Value::Bool(b) => vec![b.to_string()],
        serde_yaml::Value::Number(n) => vec![n.to_string()],
        serde_yaml::Value::Sequence(seq) => seq
            .iter()
            .flat_map(yaml_value_to_strings)
            .collect(),
        serde_yaml::Value::Null => vec![],
        serde_yaml::Value::Mapping(_) => vec![], // Skip nested objects for now
        serde_yaml::Value::Tagged(tagged) => yaml_value_to_strings(&tagged.value),
    }
}

/// Extract the content body without frontmatter.
///
/// Returns the original content if no frontmatter is present.
pub fn strip_frontmatter(content: &str) -> &str {
    let trimmed = content.trim_start();
    if !trimmed.starts_with("---") {
        return content;
    }

    let after_first = &trimmed[3..];
    if let Some(pos) = after_first.find("\n---") {
        // Skip past the closing delimiter and any following newline
        let after_closing = &after_first[pos + 4..];
        after_closing.trim_start_matches('\n')
    } else {
        content
    }
}

/// Extract wiki links from markdown content.
///
/// Wiki links use the syntax:
/// - `[[PageName]]` - links to PageName, displayed as "PageName"
/// - `[[PageName|Display Text]]` - links to PageName, displayed as "Display Text"
///
/// # Returns
/// A vector of ParsedLink structs containing the target page name
/// and optional display text.
pub fn extract_wiki_links(content: &str) -> Vec<ParsedLink> {
    let mut links = Vec::new();

    // Pattern: [[PageName]] or [[PageName|Display Text]]
    // We parse this manually for simplicity and efficiency.

    let mut i = 0;
    let content_bytes = content.as_bytes();
    let len = content.len();

    while i < len {
        // Look for [[
        if i + 1 < len && content_bytes[i] == b'[' && content_bytes[i + 1] == b'[' {
            // Found opening [[, now find the closing ]]
            let start = i + 2;
            let mut end = start;

            // Find the closing ]]
            while end + 1 < len {
                if content_bytes[end] == b']' && content_bytes[end + 1] == b']' {
                    break;
                }
                end += 1;
            }

            if end + 1 < len && content_bytes[end] == b']' && content_bytes[end + 1] == b']' {
                // Extract the content between [[ and ]]
                let link_content = &content[start..end];

                // Check if there's a pipe for display text
                if let Some(pipe_pos) = link_content.find('|') {
                    let target = link_content[..pipe_pos].trim().to_string();
                    let display = link_content[pipe_pos + 1..].trim().to_string();
                    if !target.is_empty() {
                        links.push(ParsedLink::new(target, Some(display)));
                    }
                } else {
                    let target = link_content.trim().to_string();
                    if !target.is_empty() {
                        links.push(ParsedLink::new(target, None));
                    }
                }

                i = end + 2;
                continue;
            }
        }

        i += 1;
    }

    // Remove duplicates while preserving order
    let mut seen = std::collections::HashSet::new();
    links.retain(|link| seen.insert(link.target.clone()));

    links
}

/// Parse a complete markdown file.
///
/// Extracts frontmatter metadata and wiki links from the content.
///
/// # Arguments
/// * `content` - The full markdown file content
///
/// # Returns
/// A ParsedPage containing metadata, links, and the content body.
pub fn parse_markdown(content: &str) -> ParsedPage {
    let metadata = parse_frontmatter(content);
    let body = strip_frontmatter(content);
    let links = extract_wiki_links(body);

    ParsedPage {
        metadata,
        links,
        content: body.to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_frontmatter_simple() {
        let content = r#"---
status: draft
author: jhuhta
---
# Content here"#;

        let metadata = parse_frontmatter(content);
        assert_eq!(metadata.get("status"), Some(&vec!["draft".to_string()]));
        assert_eq!(metadata.get("author"), Some(&vec!["jhuhta".to_string()]));
    }

    #[test]
    fn test_parse_frontmatter_with_list() {
        let content = r#"---
tags:
  - rust
  - wiki
  - graph
---
# Content"#;

        let metadata = parse_frontmatter(content);
        let tags = metadata.get("tags").unwrap();
        assert_eq!(tags.len(), 3);
        assert!(tags.contains(&"rust".to_string()));
        assert!(tags.contains(&"wiki".to_string()));
        assert!(tags.contains(&"graph".to_string()));
    }

    #[test]
    fn test_parse_frontmatter_empty() {
        let content = "# No frontmatter\nJust content.";
        let metadata = parse_frontmatter(content);
        assert!(metadata.is_empty());
    }

    #[test]
    fn test_parse_frontmatter_no_closing() {
        let content = "---\nstatus: draft\nNo closing delimiter";
        let metadata = parse_frontmatter(content);
        assert!(metadata.is_empty());
    }

    #[test]
    fn test_parse_frontmatter_with_numbers_and_bools() {
        let content = r#"---
count: 42
enabled: true
ratio: 3.14
---
# Content"#;

        let metadata = parse_frontmatter(content);
        assert_eq!(metadata.get("count"), Some(&vec!["42".to_string()]));
        assert_eq!(metadata.get("enabled"), Some(&vec!["true".to_string()]));
        assert_eq!(metadata.get("ratio"), Some(&vec!["3.14".to_string()]));
    }

    #[test]
    fn test_strip_frontmatter() {
        let content = r#"---
status: draft
---
# Title

Content here."#;

        let body = strip_frontmatter(content);
        assert!(body.starts_with("# Title"));
        assert!(body.contains("Content here."));
        assert!(!body.contains("status: draft"));
    }

    #[test]
    fn test_strip_frontmatter_no_frontmatter() {
        let content = "# Title\n\nContent here.";
        let body = strip_frontmatter(content);
        assert_eq!(body, content);
    }

    #[test]
    fn test_extract_wiki_links_simple() {
        let content = "This links to [[HomePage]] and [[About]].";
        let links = extract_wiki_links(content);

        assert_eq!(links.len(), 2);
        assert_eq!(links[0].target, "HomePage");
        assert!(links[0].display_text.is_none());
        assert_eq!(links[1].target, "About");
    }

    #[test]
    fn test_extract_wiki_links_with_display_text() {
        let content = "Check out [[HomePage|the home page]] for more info.";
        let links = extract_wiki_links(content);

        assert_eq!(links.len(), 1);
        assert_eq!(links[0].target, "HomePage");
        assert_eq!(links[0].display_text, Some("the home page".to_string()));
    }

    #[test]
    fn test_extract_wiki_links_mixed() {
        let content = r#"
# Links

See [[HomePage]] for the main page.
Also check [[About|About Us]] and [[Contact]].
        "#;

        let links = extract_wiki_links(content);
        assert_eq!(links.len(), 3);
        assert_eq!(links[0].target, "HomePage");
        assert_eq!(links[1].target, "About");
        assert_eq!(links[1].display_text, Some("About Us".to_string()));
        assert_eq!(links[2].target, "Contact");
    }

    #[test]
    fn test_extract_wiki_links_duplicates_removed() {
        let content = "[[Page]] links to [[Page]] twice.";
        let links = extract_wiki_links(content);
        assert_eq!(links.len(), 1);
    }

    #[test]
    fn test_extract_wiki_links_empty_content() {
        let content = "";
        let links = extract_wiki_links(content);
        assert!(links.is_empty());
    }

    #[test]
    fn test_extract_wiki_links_no_links() {
        let content = "This is just regular [markdown](http://example.com) content.";
        let links = extract_wiki_links(content);
        assert!(links.is_empty());
    }

    #[test]
    fn test_extract_wiki_links_whitespace_trimmed() {
        let content = "[[ SpacedPage | Display Text ]]";
        let links = extract_wiki_links(content);
        assert_eq!(links.len(), 1);
        assert_eq!(links[0].target, "SpacedPage");
        assert_eq!(links[0].display_text, Some("Display Text".to_string()));
    }

    #[test]
    fn test_parse_markdown_complete() {
        let content = r#"---
status: published
tags:
  - rust
  - wiki
---
# Welcome

This page links to [[HomePage]] and [[About|About Us]].
"#;

        let parsed = parse_markdown(content);

        // Check metadata
        assert_eq!(
            parsed.metadata.get("status"),
            Some(&vec!["published".to_string()])
        );
        assert_eq!(parsed.metadata.get("tags").unwrap().len(), 2);

        // Check links
        assert_eq!(parsed.links.len(), 2);
        assert_eq!(parsed.links[0].target, "HomePage");
        assert_eq!(parsed.links[1].target, "About");

        // Check content
        assert!(parsed.content.starts_with("# Welcome"));
    }
}
