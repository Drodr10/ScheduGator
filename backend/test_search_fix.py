from brain import GemmaBrain

brain = GemmaBrain()
result = brain.search_catalog_tool(queries=['COP', 'CIS'], min_level=4000, max_level=4999)

print('Status:', result.get('status'))
print('Number of result groups:', len(result.get('results', [])) if result.get('results') else 0)

for group in result.get('results', []):
    print(f"  Query '{group['query']}': {group['count']} courses")
    if group['results']:
        codes = [c['code'] for c in group['results'][:3]]
        print(f"    Examples: {codes}")
