//! Graph event types for file watching notifications.
//!
//! This module defines events that are emitted when the wiki graph changes
//! due to file system modifications.

use pyo3::prelude::*;
use std::collections::VecDeque;
use std::sync::{Arc, Mutex};

/// Events emitted when the graph changes.
///
/// These events are produced by the file watcher and can be
/// polled from Python for real-time UI updates.
#[pyclass]
#[derive(Clone, Debug, PartialEq)]
pub enum GraphEvent {
    /// A new page was created (new .md file)
    PageCreated { name: String },

    /// An existing page was updated (file modified)
    PageUpdated { name: String },

    /// A page was deleted (file removed)
    PageDeleted { name: String },

    /// A new link was added between pages
    LinkCreated { from: String, to: String },

    /// A link was removed between pages
    LinkRemoved { from: String, to: String },
}

#[pymethods]
impl GraphEvent {
    /// Get the event type as a string.
    ///
    /// Returns one of: "page_created", "page_updated", "page_deleted",
    /// "link_created", "link_removed"
    fn event_type(&self) -> &str {
        match self {
            GraphEvent::PageCreated { .. } => "page_created",
            GraphEvent::PageUpdated { .. } => "page_updated",
            GraphEvent::PageDeleted { .. } => "page_deleted",
            GraphEvent::LinkCreated { .. } => "link_created",
            GraphEvent::LinkRemoved { .. } => "link_removed",
        }
    }

    /// Get the primary page name associated with the event.
    ///
    /// Returns the page name for page events, None for link events.
    fn page_name(&self) -> Option<String> {
        match self {
            GraphEvent::PageCreated { name } => Some(name.clone()),
            GraphEvent::PageUpdated { name } => Some(name.clone()),
            GraphEvent::PageDeleted { name } => Some(name.clone()),
            _ => None,
        }
    }

    /// Get the source page for link events.
    ///
    /// Returns the "from" page for link events, None for page events.
    fn link_from(&self) -> Option<String> {
        match self {
            GraphEvent::LinkCreated { from, .. } => Some(from.clone()),
            GraphEvent::LinkRemoved { from, .. } => Some(from.clone()),
            _ => None,
        }
    }

    /// Get the target page for link events.
    ///
    /// Returns the "to" page for link events, None for page events.
    fn link_to(&self) -> Option<String> {
        match self {
            GraphEvent::LinkCreated { to, .. } => Some(to.clone()),
            GraphEvent::LinkRemoved { to, .. } => Some(to.clone()),
            _ => None,
        }
    }

    fn __repr__(&self) -> String {
        match self {
            GraphEvent::PageCreated { name } => format!("GraphEvent.PageCreated('{}')", name),
            GraphEvent::PageUpdated { name } => format!("GraphEvent.PageUpdated('{}')", name),
            GraphEvent::PageDeleted { name } => format!("GraphEvent.PageDeleted('{}')", name),
            GraphEvent::LinkCreated { from, to } => {
                format!("GraphEvent.LinkCreated('{}' -> '{}')", from, to)
            }
            GraphEvent::LinkRemoved { from, to } => {
                format!("GraphEvent.LinkRemoved('{}' -> '{}')", from, to)
            }
        }
    }
}

/// Thread-safe event queue for communication between watcher and main thread.
///
/// Uses Arc<Mutex<VecDeque>> for Send + Sync compatibility with PyO3.
#[derive(Clone)]
pub struct EventQueue {
    inner: Arc<Mutex<VecDeque<GraphEvent>>>,
}

impl EventQueue {
    /// Create a new empty event queue.
    pub fn new() -> Self {
        Self {
            inner: Arc::new(Mutex::new(VecDeque::new())),
        }
    }

    /// Push an event to the queue.
    pub fn push(&self, event: GraphEvent) {
        if let Ok(mut queue) = self.inner.lock() {
            queue.push_back(event);
        }
    }

    /// Push multiple events to the queue.
    pub fn push_all(&self, events: Vec<GraphEvent>) {
        if let Ok(mut queue) = self.inner.lock() {
            for event in events {
                queue.push_back(event);
            }
        }
    }

    /// Drain all events from the queue.
    ///
    /// Returns all queued events and clears the queue.
    pub fn drain_all(&self) -> Vec<GraphEvent> {
        if let Ok(mut queue) = self.inner.lock() {
            queue.drain(..).collect()
        } else {
            Vec::new()
        }
    }

    /// Check if queue is empty.
    pub fn is_empty(&self) -> bool {
        self.inner.lock().map(|q| q.is_empty()).unwrap_or(true)
    }

    /// Get the number of pending events.
    pub fn len(&self) -> usize {
        self.inner.lock().map(|q| q.len()).unwrap_or(0)
    }
}

impl Default for EventQueue {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;

    #[test]
    fn test_event_queue_push_and_drain() {
        let queue = EventQueue::new();
        queue.push(GraphEvent::PageCreated {
            name: "Test".to_string(),
        });
        queue.push(GraphEvent::PageUpdated {
            name: "Test".to_string(),
        });

        assert_eq!(queue.len(), 2);
        assert!(!queue.is_empty());

        let events = queue.drain_all();
        assert_eq!(events.len(), 2);
        assert!(queue.is_empty());
    }

    #[test]
    fn test_event_queue_push_all() {
        let queue = EventQueue::new();
        queue.push_all(vec![
            GraphEvent::PageCreated {
                name: "A".to_string(),
            },
            GraphEvent::PageCreated {
                name: "B".to_string(),
            },
            GraphEvent::PageCreated {
                name: "C".to_string(),
            },
        ]);

        assert_eq!(queue.len(), 3);
    }

    #[test]
    fn test_event_queue_thread_safety() {
        let queue = EventQueue::new();
        let queue_clone = queue.clone();

        let handle = thread::spawn(move || {
            for i in 0..100 {
                queue_clone.push(GraphEvent::PageCreated {
                    name: format!("Page{}", i),
                });
            }
        });

        handle.join().unwrap();
        let events = queue.drain_all();
        assert_eq!(events.len(), 100);
    }

    #[test]
    fn test_graph_event_type() {
        let event = GraphEvent::PageCreated {
            name: "Test".to_string(),
        };
        assert_eq!(event.event_type(), "page_created");
        assert_eq!(event.page_name(), Some("Test".to_string()));
        assert_eq!(event.link_from(), None);
        assert_eq!(event.link_to(), None);

        let link_event = GraphEvent::LinkCreated {
            from: "A".to_string(),
            to: "B".to_string(),
        };
        assert_eq!(link_event.event_type(), "link_created");
        assert_eq!(link_event.page_name(), None);
        assert_eq!(link_event.link_from(), Some("A".to_string()));
        assert_eq!(link_event.link_to(), Some("B".to_string()));
    }

    #[test]
    fn test_graph_event_repr() {
        let event = GraphEvent::PageCreated {
            name: "Test".to_string(),
        };
        assert!(event.__repr__().contains("PageCreated"));
        assert!(event.__repr__().contains("Test"));

        let link_event = GraphEvent::LinkCreated {
            from: "A".to_string(),
            to: "B".to_string(),
        };
        assert!(link_event.__repr__().contains("LinkCreated"));
        assert!(link_event.__repr__().contains("A"));
        assert!(link_event.__repr__().contains("B"));
    }
}
