"""C++ library/feature to Rust equivalent mappings."""

CPP_CRATE_MAP = {
    # STL containers
    "std::vector": "Vec<T>",
    "std::string": "String",
    "std::map": "std::collections::HashMap<K, V>",
    "std::unordered_map": "std::collections::HashMap<K, V>",
    "std::set": "std::collections::HashSet<T>",
    
    # Smart pointers
    "std::shared_ptr": "std::sync::Arc<T> (thread-safe) or std::rc::Rc<T> (single-threaded)",
    "std::unique_ptr": "Box<T>",
    "std::weak_ptr": "std::sync::Weak<T> or std::rc::Weak<T>",
    
    # Threading
    "std::thread": "std::thread",
    "std::mutex": "std::sync::Mutex<T>",
    "pthread": "std::thread",
    
    # Libraries
    "boost::asio": "tokio = \"1\" (async runtime)",
    "boost::filesystem": "std::fs (built-in)",
    "openssl": "openssl = \"0.10\" or rustls = \"0.21\"",
}


def get_rust_equivalent(cpp_feature: str) -> str:
    """Get Rust equivalent for C++ feature."""
    return CPP_CRATE_MAP.get(cpp_feature, f"# TODO: Find Rust equivalent for {cpp_feature}")

