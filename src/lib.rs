use pyo3_polars::PolarsAllocator;

mod expressions;

// Share Polars' allocator so Series allocated here can be freed by Polars.
#[global_allocator]
static ALLOC: PolarsAllocator = PolarsAllocator::new();
