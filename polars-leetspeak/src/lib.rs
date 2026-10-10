mod expressions;

/// Routing the plugin's allocations through the host process's Polars allocator
/// avoids a second, independent allocator inside the shared object.
#[global_allocator]
static ALLOC: pyo3_polars::PolarsAllocator = pyo3_polars::PolarsAllocator::new();
