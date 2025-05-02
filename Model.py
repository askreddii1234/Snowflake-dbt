#!/usr/bin/env python
"""
Deduplication Model Generator

This script scans dbt source YAML files, identifies tables with dedup_keys,
and generates corresponding deduplication models.

Usage:
    python dedup_generator.py --sources-dir <sources_directory> --output-dir <output_directory>

Example:
    python dedup_generator.py --sources-dir models/sources --output-dir models/dedup_table

"""

import os
import yaml
import argparse
from pathlib import Path


def load_source_yaml(file_path):
    """Load a dbt source YAML file.
    
    Args:
        file_path (str): Path to the source YAML file
        
    Returns:
        dict: Parsed YAML content
    """
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def find_tables_with_dedup_keys(source_yaml):
    """Find all tables with dedup_key defined in the source YAML.
    
    Args:
        source_yaml (dict): Parsed source YAML content
        
    Returns:
        list: Tables with dedup_keys and their metadata
    """
    tables_with_dedup = []
    
    if not source_yaml or 'sources' not in source_yaml:
        return tables_with_dedup
    
    for source in source_yaml['sources']:
        source_name = source.get('name')
        database = source.get('database')
        schema = source.get('schema')
        
        if 'tables' not in source:
            continue
            
        for table in source['tables']:
            table_name = table.get('name')
            meta = table.get('meta', {})
            
            if meta and 'dedup_key' in meta:
                dedup_key = meta['dedup_key']
                tables_with_dedup.append({
                    'source_name': source_name,
                    'database': database,
                    'schema': schema,
                    'table_name': table_name,
                    'dedup_key': dedup_key
                })
    
    return tables_with_dedup


def generate_dedup_model(table_info, output_dir, client_schema_filter=False):
    """Generate a deduplication model SQL file for a table.
    
    Args:
        table_info (dict): Table metadata
        output_dir (str): Directory to output the model
        client_schema_filter (bool): Whether to add client schema filtering
        
    Returns:
        str: Path to the generated model file
    """
    source_name = table_info['source_name']
    table_name = table_info['table_name']
    dedup_key = table_info['dedup_key']
    
    model_name = f"dedup_{table_name}.sql"
    model_path = os.path.join(output_dir, model_name)
    
    # Create model content with or without client schema filtering
    if client_schema_filter:
        model_content = f"""/*
    Deduplicate {table_name} data
*/
WITH source_data AS (
  SELECT *
  FROM {{{{ source('{source_name}', '{table_name}') }}}}
  WHERE {{{{ client_schema_filter('schema_name') }}}}
)
SELECT *
FROM {{{{ dedup_query(
    query='source_data',
    composite_primary_key='{dedup_key}'
) }}}}
"""
    else:
        model_content = f"""/*
    Deduplicate {table_name} data
*/
WITH source_data AS (
  SELECT *
  FROM {{{{ source('{source_name}', '{table_name}') }}}}
)
SELECT *
FROM {{{{ dedup_query(
    query='source_data',
    composite_primary_key='{dedup_key}'
) }}}}
"""
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Write the model file
    with open(model_path, 'w') as file:
        file.write(model_content)
    
    return model_path


def main():
    """Main function to parse arguments and generate models."""
    parser = argparse.ArgumentParser(description='Generate DBT deduplication models from source YAML files.')
    parser.add_argument('--sources-dir', required=True, help='Directory containing source YAML files')
    parser.add_argument('--output-dir', required=True, help='Directory to output deduplication models')
    parser.add_argument('--client-schema-filter', action='store_true', 
                        help='Add client_schema_filter to the models')
    
    args = parser.parse_args()
    
    # Find all .yml files in the sources directory
    source_files = list(Path(args.sources_dir).glob('**/*.yml'))
    
    total_dedup_tables = 0
    generated_files = []
    
    # Process each source file
    for source_file in source_files:
        print(f"Processing source file: {source_file}")
        source_yaml = load_source_yaml(source_file)
        dedup_tables = find_tables_with_dedup_keys(source_yaml)
        
        for table_info in dedup_tables:
            model_path = generate_dedup_model(
                table_info, 
                args.output_dir,
                args.client_schema_filter
            )
            generated_files.append(model_path)
            total_dedup_tables += 1
    
    # Report results
    print(f"\nTotal deduplication models generated: {total_dedup_tables}")
    if total_dedup_tables > 0:
        print("\nGenerated models:")
        for file_path in generated_files:
            print(f"  - {file_path}")


if __name__ == "__main__":
    main()
