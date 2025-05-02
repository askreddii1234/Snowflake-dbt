#!/bin/bash
# Test script for the deduplication model generator

# Create test directories
mkdir -p test_sources
mkdir -p test_output

# Copy the core_db.yml to the test_sources directory
echo "Copying core_db.yml to test_sources directory..."
cp core_db.yml test_sources/

# Run the deduplication generator
echo "Running deduplication generator..."
python dedup_generator.py --sources-dir test_sources --output-dir test_output

# Check the generated files
echo "Generated files:"
ls -la test_output/

# Display content of the first generated file
echo "Content of the first generated file:"
head -20 test_output/dedup_account_auth_limit.sql

# Count tables with dedup keys in the source file
echo "Counting tables with dedup keys in source file..."
dedup_count=$(grep -c "dedup_key:" test_sources/core_db.yml)
echo "Number of tables with dedup_key in source file: $dedup_count"

# Count generated files
gen_count=$(ls -1 test_output/ | wc -l)
echo "Number of generated files: $gen_count"

# Verify counts match
if [ "$dedup_count" -eq "$gen_count" ]; then
    echo "PASS: All deduplication models were generated correctly."
else
    echo "FAIL: Number of generated models doesn't match number of tables with dedup_key."
fi

# Test with client schema filtering
echo "Testing with client schema filtering..."
python dedup_generator.py --sources-dir test_sources --output-dir test_output_with_filter --client-schema-filter

# Compare generated files
echo "Comparing standard vs. filtered models:"
echo "Standard model (first few lines):"
head -10 test_output/dedup_account_auth_limit.sql
echo "Filtered model (first few lines):"
head -10 test_output_with_filter/dedup_account_auth_limit.sql

# Cleanup
echo "Do you want to clean up test directories? (y/n)"
read cleanup
if [ "$cleanup" = "y" ]; then
    rm -rf test_sources
    rm -rf test_output
    rm -rf test_output_with_filter
    echo "Test directories cleaned up."
fi
