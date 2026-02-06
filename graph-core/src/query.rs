//! Query engine for filtering wiki pages by metadata and links.
//!
//! This module provides the Filter enum and MetaTable result types
//! for querying wiki pages. Filters support metadata matching and
//! link relationship queries.

use crate::graph::WikiGraph;
use crate::models::PageNode;
use pyo3::prelude::*;
use regex::Regex;
use std::collections::HashMap;

/// Filter types for querying wiki pages.
///
/// All filters can be combined with AND logic (all must match).
#[derive(Clone, Debug)]
pub enum Filter {
    /// Match pages where metadata[key] contains the exact value.
    Equals { key: String, value: String },

    /// Match pages that have the specified metadata key (any value).
    HasKey { key: String },

    /// Match pages where any value in metadata[key] contains the substring.
    Contains { key: String, substring: String },

    /// Match pages where any value in metadata[key] matches the regex pattern.
    Matches { key: String, pattern: String },

    /// Match pages that link to the specified target page.
    LinksTo { page: String },

    /// Match pages that are linked from the specified source page.
    LinkedFrom { page: String },
}

impl Filter {
    /// Check if a page matches this filter.
    ///
    /// For link-based filters, requires access to the graph.
    pub fn matches_page(&self, page: &PageNode, graph: &WikiGraph) -> bool {
        match self {
            Filter::Equals { key, value } => page
                .metadata
                .get(key)
                .map(|values| values.contains(value))
                .unwrap_or(false),

            Filter::HasKey { key } => page.metadata.contains_key(key),

            Filter::Contains { key, substring } => page
                .metadata
                .get(key)
                .map(|values| values.iter().any(|v| v.contains(substring)))
                .unwrap_or(false),

            Filter::Matches { key, pattern } => {
                match Regex::new(pattern) {
                    Ok(re) => page
                        .metadata
                        .get(key)
                        .map(|values| values.iter().any(|v| re.is_match(v)))
                        .unwrap_or(false),
                    Err(_) => false, // Invalid regex returns no match
                }
            }

            Filter::LinksTo { page: target } => {
                // Check if this page links to the target
                graph.get_outlinks(&page.name).contains(target)
            }

            Filter::LinkedFrom { page: source } => {
                // Check if this page is linked from the source (has backlink)
                graph.get_backlinks(&page.name).contains(source)
            }
        }
    }
}

/// Check if a page matches all filters (AND logic).
pub fn matches_all_filters(page: &PageNode, filters: &[Filter], graph: &WikiGraph) -> bool {
    filters.iter().all(|f| f.matches_page(page, graph))
}

/// Python-facing Filter wrapper class.
///
/// Provides static factory methods for creating filters in Python:
/// ```python
/// from graph_core import Filter
///
/// f1 = Filter.equals("status", "draft")
/// f2 = Filter.has_key("tags")
/// f3 = Filter.contains("tags", "rust")
/// f4 = Filter.matches("version", r"v\d+")
/// f5 = Filter.links_to("HomePage")
/// f6 = Filter.linked_from("Index")
/// ```
#[pyclass(name = "Filter")]
#[derive(Clone)]
pub struct PyFilter {
    pub(crate) inner: Filter,
}

#[pymethods]
impl PyFilter {
    /// Create an Equals filter: metadata[key] contains the exact value.
    ///
    /// # Arguments
    /// * `key` - The metadata key to check
    /// * `value` - The exact value to match
    ///
    /// # Example
    /// ```python
    /// # Find all pages with status == "draft"
    /// filter = Filter.equals("status", "draft")
    /// ```
    #[staticmethod]
    fn equals(key: String, value: String) -> Self {
        Self {
            inner: Filter::Equals { key, value },
        }
    }

    /// Create a HasKey filter: metadata contains the specified key.
    ///
    /// # Arguments
    /// * `key` - The metadata key to check for existence
    ///
    /// # Example
    /// ```python
    /// # Find all pages that have a "priority" field
    /// filter = Filter.has_key("priority")
    /// ```
    #[staticmethod]
    fn has_key(key: String) -> Self {
        Self {
            inner: Filter::HasKey { key },
        }
    }

    /// Create a Contains filter: any value in metadata[key] contains substring.
    ///
    /// # Arguments
    /// * `key` - The metadata key to check
    /// * `substring` - The substring to search for
    ///
    /// # Example
    /// ```python
    /// # Find pages with any tag containing "rust"
    /// filter = Filter.contains("tags", "rust")
    /// ```
    #[staticmethod]
    fn contains(key: String, substring: String) -> Self {
        Self {
            inner: Filter::Contains { key, substring },
        }
    }

    /// Create a Matches filter: any value in metadata[key] matches regex.
    ///
    /// # Arguments
    /// * `key` - The metadata key to check
    /// * `pattern` - The regex pattern to match
    ///
    /// # Example
    /// ```python
    /// # Find pages with version matching semver pattern
    /// filter = Filter.matches("version", r"v\d+\.\d+\.\d+")
    /// ```
    #[staticmethod]
    fn matches(key: String, pattern: String) -> Self {
        Self {
            inner: Filter::Matches { key, pattern },
        }
    }

    /// Create a LinksTo filter: page links to the specified target.
    ///
    /// # Arguments
    /// * `page` - The target page name
    ///
    /// # Example
    /// ```python
    /// # Find all pages that link to HomePage
    /// filter = Filter.links_to("HomePage")
    /// ```
    #[staticmethod]
    fn links_to(page: String) -> Self {
        Self {
            inner: Filter::LinksTo { page },
        }
    }

    /// Create a LinkedFrom filter: page is linked from the source.
    ///
    /// # Arguments
    /// * `page` - The source page name
    ///
    /// # Example
    /// ```python
    /// # Find all pages linked from the Index page
    /// filter = Filter.linked_from("Index")
    /// ```
    #[staticmethod]
    fn linked_from(page: String) -> Self {
        Self {
            inner: Filter::LinkedFrom { page },
        }
    }

    fn __repr__(&self) -> String {
        match &self.inner {
            Filter::Equals { key, value } => format!("Filter.equals('{}', '{}')", key, value),
            Filter::HasKey { key } => format!("Filter.has_key('{}')", key),
            Filter::Contains { key, substring } => {
                format!("Filter.contains('{}', '{}')", key, substring)
            }
            Filter::Matches { key, pattern } => {
                format!("Filter.matches('{}', '{}')", key, pattern)
            }
            Filter::LinksTo { page } => format!("Filter.links_to('{}')", page),
            Filter::LinkedFrom { page } => format!("Filter.linked_from('{}')", page),
        }
    }
}

/// A row in a MetaTable result.
#[pyclass]
#[derive(Clone, Debug)]
pub struct MetaTableRow {
    /// The page name (always included)
    #[pyo3(get)]
    pub page_name: String,

    /// Selected column values
    #[pyo3(get)]
    pub values: HashMap<String, Vec<String>>,
}

#[pymethods]
impl MetaTableRow {
    /// Get a column value, returns empty list if not present.
    ///
    /// # Arguments
    /// * `column` - The column name to retrieve
    ///
    /// # Returns
    /// The values for the column, or empty list if not present.
    fn get(&self, column: &str) -> Vec<String> {
        self.values.get(column).cloned().unwrap_or_default()
    }

    fn __repr__(&self) -> String {
        format!(
            "MetaTableRow(page='{}', values={:?})",
            self.page_name, self.values
        )
    }
}

/// Result of a metatable query.
#[pyclass]
#[derive(Clone, Debug)]
pub struct MetaTableResult {
    /// The columns that were requested
    #[pyo3(get)]
    pub columns: Vec<String>,

    /// The matching rows
    #[pyo3(get)]
    pub rows: Vec<MetaTableRow>,
}

#[pymethods]
impl MetaTableResult {
    /// Get the number of rows.
    fn __len__(&self) -> usize {
        self.rows.len()
    }

    /// Check if result is empty.
    fn is_empty(&self) -> bool {
        self.rows.is_empty()
    }

    /// Iterate over rows.
    fn __iter__(slf: PyRef<'_, Self>) -> PyResult<Py<MetaTableRowIterator>> {
        let iter = MetaTableRowIterator {
            inner: slf.rows.clone().into_iter(),
        };
        Py::new(slf.py(), iter)
    }

    fn __repr__(&self) -> String {
        format!(
            "MetaTableResult(columns={:?}, rows={})",
            self.columns,
            self.rows.len()
        )
    }
}

/// Iterator for MetaTableResult rows.
#[pyclass]
pub struct MetaTableRowIterator {
    inner: std::vec::IntoIter<MetaTableRow>,
}

#[pymethods]
impl MetaTableRowIterator {
    fn __next__(&mut self) -> Option<MetaTableRow> {
        self.inner.next()
    }

    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use std::time::SystemTime;

    fn test_page(name: &str, metadata: Vec<(&str, Vec<&str>)>) -> PageNode {
        let mut meta = HashMap::new();
        for (k, v) in metadata {
            meta.insert(k.to_string(), v.iter().map(|s| s.to_string()).collect());
        }
        PageNode::with_metadata(
            name.to_string(),
            PathBuf::from(format!("{}.md", name)),
            meta,
            SystemTime::now(),
        )
    }

    #[test]
    fn test_filter_equals() {
        let page = test_page("Test", vec![("status", vec!["draft"])]);
        let graph = WikiGraph::new();

        let filter = Filter::Equals {
            key: "status".to_string(),
            value: "draft".to_string(),
        };
        assert!(filter.matches_page(&page, &graph));

        let filter = Filter::Equals {
            key: "status".to_string(),
            value: "published".to_string(),
        };
        assert!(!filter.matches_page(&page, &graph));
    }

    #[test]
    fn test_filter_equals_multi_value() {
        let page = test_page("Test", vec![("tags", vec!["rust", "wiki", "graph"])]);
        let graph = WikiGraph::new();

        // Should match any value in the list
        let filter = Filter::Equals {
            key: "tags".to_string(),
            value: "wiki".to_string(),
        };
        assert!(filter.matches_page(&page, &graph));
    }

    #[test]
    fn test_filter_has_key() {
        let page = test_page("Test", vec![("status", vec!["draft"])]);
        let graph = WikiGraph::new();

        assert!(Filter::HasKey {
            key: "status".to_string()
        }
        .matches_page(&page, &graph));
        assert!(!Filter::HasKey {
            key: "missing".to_string()
        }
        .matches_page(&page, &graph));
    }

    #[test]
    fn test_filter_contains() {
        let page = test_page("Test", vec![("tags", vec!["rust-lang", "wiki"])]);
        let graph = WikiGraph::new();

        let filter = Filter::Contains {
            key: "tags".to_string(),
            substring: "rust".to_string(),
        };
        assert!(filter.matches_page(&page, &graph));

        let filter = Filter::Contains {
            key: "tags".to_string(),
            substring: "python".to_string(),
        };
        assert!(!filter.matches_page(&page, &graph));
    }

    #[test]
    fn test_filter_matches_regex() {
        let page = test_page("Test", vec![("version", vec!["v1.2.3"])]);
        let graph = WikiGraph::new();

        let filter = Filter::Matches {
            key: "version".to_string(),
            pattern: r"v\d+\.\d+\.\d+".to_string(),
        };
        assert!(filter.matches_page(&page, &graph));

        let filter = Filter::Matches {
            key: "version".to_string(),
            pattern: r"v\d+\.\d+\.\d+\.\d+".to_string(), // Requires 4 components
        };
        assert!(!filter.matches_page(&page, &graph));
    }

    #[test]
    fn test_filter_invalid_regex() {
        let page = test_page("Test", vec![("text", vec!["hello"])]);
        let graph = WikiGraph::new();

        let filter = Filter::Matches {
            key: "text".to_string(),
            pattern: r"[invalid".to_string(), // Unclosed bracket
        };
        assert!(!filter.matches_page(&page, &graph)); // Invalid regex = no match
    }

    #[test]
    fn test_filter_missing_key() {
        let page = test_page("Test", vec![("status", vec!["draft"])]);
        let graph = WikiGraph::new();

        // All filters should return false for missing keys
        assert!(!Filter::Equals {
            key: "missing".to_string(),
            value: "any".to_string()
        }
        .matches_page(&page, &graph));

        assert!(!Filter::Contains {
            key: "missing".to_string(),
            substring: "any".to_string()
        }
        .matches_page(&page, &graph));

        assert!(!Filter::Matches {
            key: "missing".to_string(),
            pattern: ".*".to_string()
        }
        .matches_page(&page, &graph));
    }

    #[test]
    fn test_matches_all_filters() {
        let page = test_page(
            "Test",
            vec![("status", vec!["draft"]), ("author", vec!["alice"])],
        );
        let graph = WikiGraph::new();

        // Both filters match
        let filters = vec![
            Filter::Equals {
                key: "status".to_string(),
                value: "draft".to_string(),
            },
            Filter::Equals {
                key: "author".to_string(),
                value: "alice".to_string(),
            },
        ];
        assert!(matches_all_filters(&page, &filters, &graph));

        // One filter doesn't match
        let filters = vec![
            Filter::Equals {
                key: "status".to_string(),
                value: "draft".to_string(),
            },
            Filter::Equals {
                key: "author".to_string(),
                value: "bob".to_string(),
            },
        ];
        assert!(!matches_all_filters(&page, &filters, &graph));

        // Empty filters = all pages match
        assert!(matches_all_filters(&page, &[], &graph));
    }
}
