{# macros/generate_dedup_models.sql #}

{% macro generate_dedup_models(schema_name=none) %}
  
  {# Set the default schema name based on vars if none is provided #}
  {% if schema_name is none %}
    {% set schema_name = var('source_schema', 'GALILEO_RAW') %}
  {% endif %}
  
  {# Get all sources from the project #}
  {% set sources = graph.sources.values() %}
  
  {# Filter sources by schema if specified #}
  {% if schema_name %}
    {% set sources = sources | selectattr('schema', 'equalto', schema_name) | list %}
  {% endif %}
  
  {# Iterate through each source to find tables with dedup_keys #}
  {% for source in sources %}
    {# Get the source name and schema #}
    {% set source_name = source.source_name %}
    {% set source_schema = source.schema %}
    
    {# Get tables for this source from the original YAML #}
    {% set tables = source.tables.values() %}
    
    {# Process each table to find those with dedup_keys #}
    {% for table in tables %}
      {% set table_name = table.name %}
      
      {# Check if table has dedup_key in its meta #}
      {% if table.meta and table.meta.get('dedup_key') %}
        {% set dedup_key = table.meta.get('dedup_key') %}
        
        {# Generate the deduplication model SQL #}
        {{ log('Generating deduplication model for ' ~ source_name ~ '.' ~ table_name ~ ' with dedup_key: ' ~ dedup_key, info=True) }}
        
        {# Define the output model name #}
        {% set model_name = 'dedup_' ~ table_name %}
        
        {# Create the deduplication model content #}
{{ 
'/*
    Deduplicate ' ~ table_name ~ ' data - Auto Generated
*/
WITH source_data AS (
  SELECT *
  FROM {{ source(\'' ~ source_name ~ '\', \'' ~ table_name ~ '\') }}
)
SELECT *
FROM {{ dedup_query(
    query=\'source_data\',
    composite_primary_key=\'' ~ dedup_key ~ '\'
) }}' 
}}

      {% endif %}
    {% endfor %}
  {% endfor %}
  
  {{ return('Deduplication models generation complete.') }}
{% endmacro %}
