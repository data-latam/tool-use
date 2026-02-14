# Evaluation Rubric for Colosseum Travel Planning

## TURN 1: Get Historical Information

### RUBRIC 1
- **CRITERIA**: Must use `wikipedia.get_summary` tool to retrieve information about the Colosseum
- **CATEGORY**: Tool Selection
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: Wikipedia is the appropriate authoritative source for factual historical information about landmarks. The user explicitly asked about when it was built and its original purpose.

### RUBRIC 2
- **CRITERIA**: Wikipedia query must include "Colosseum" as the title parameter
- **CATEGORY**: Query Construction
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: The correct title ensures retrieval of the relevant Wikipedia article about the Roman landmark.

### RUBRIC 3
- **CRITERIA**: Must NOT use `ddg-search.search` as the primary tool for historical information when Wikipedia is available
- **CATEGORY**: Tool Selection
- **TYPE**: Negated
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: Wikipedia provides more authoritative and structured historical information than web search results.

---

## TURN 2: Geocode Colosseum Location

### RUBRIC 4
- **CRITERIA**: Must use `google-maps.maps_geocode` tool to get the Colosseum's coordinates
- **CATEGORY**: Tool Selection
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: Geocoding is required to obtain latitude/longitude coordinates for the subsequent proximity-based restaurant search.

### RUBRIC 5
- **CRITERIA**: Geocode address must include "Colosseum" and "Rome" or "Italy"
- **CATEGORY**: Query Construction
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: Including location context ensures the correct landmark is geocoded (not other colosseums worldwide).

### RUBRIC 6
- **CRITERIA**: Must NOT use `osm-mcp-server.geocode_address` when `google-maps.maps_geocode` is available for this task
- **CATEGORY**: Tool Selection
- **TYPE**: Negated
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: Google Maps geocoding integrates better with subsequent Google Maps tools (places, directions).

---

## TURN 3: Search for Nearby Restaurants

### RUBRIC 7
- **CRITERIA**: Must use `google-maps.maps_search_places` tool to find restaurants near the Colosseum
- **CATEGORY**: Tool Selection
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: This tool enables proximity-based search with ratings, which is necessary to find highly-rated restaurants within 1km.

### RUBRIC 8
- **CRITERIA**: Search query must include terms related to Italian food (e.g., "Italian restaurant", "traditional Italian", "trattoria")
- **CATEGORY**: Query Construction
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: The user specifically requested traditional Italian food recommendations.

### RUBRIC 9
- **CRITERIA**: Search must use the Colosseum coordinates obtained from geocoding (approximately 41.89, 12.49)
- **CATEGORY**: Query Construction
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: Using the correct coordinates ensures restaurants are actually near the Colosseum.

### RUBRIC 10
- **CRITERIA**: Search radius must be set to approximately 1000 meters (1km) as requested
- **CATEGORY**: Query Construction
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: The user explicitly requested restaurants within 1km of the Colosseum.

### RUBRIC 11
- **CRITERIA**: Must NOT use `osm-mcp-server.find_nearby_places` when `google-maps.maps_search_places` is available
- **CATEGORY**: Tool Selection
- **TYPE**: Negated
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: Google Maps provides ratings and reviews which are necessary to recommend "highly-rated" restaurants.

---

## TURN 4: Geocode Termini Station

### RUBRIC 12
- **CRITERIA**: Must use `google-maps.maps_geocode` tool to get Termini Station's location
- **CATEGORY**: Tool Selection
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: The starting point coordinates are needed for calculating walking directions.

### RUBRIC 13
- **CRITERIA**: Geocode address must include "Termini" and "Rome" or "Roma"
- **CATEGORY**: Query Construction
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: Specific address ensures the correct train station in Rome is identified.

---

## TURN 5: Get Walking Directions

### RUBRIC 14
- **CRITERIA**: Must use `google-maps.maps_directions` tool to get directions from Termini to Colosseum
- **CATEGORY**: Tool Selection
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: This tool provides route information including distance and estimated walking time.

### RUBRIC 15
- **CRITERIA**: Direction mode must be set to "walking" (not driving, transit, or bicycling)
- **CATEGORY**: Query Construction
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: The user explicitly asked for walking directions and walking time.

### RUBRIC 16
- **CRITERIA**: Origin must be Termini Station and destination must be the Colosseum
- **CATEGORY**: Query Construction
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: The user is staying near Termini and wants to walk to the Colosseum.

### RUBRIC 17
- **CRITERIA**: Must NOT use `osm-mcp-server.get_route_directions` when `google-maps.maps_directions` is available
- **CATEGORY**: Tool Selection
- **TYPE**: Negated
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: Google Maps directions integrate with elevation data for comprehensive mobility assessment.

---

## TURN 6: Check Elevation for Mobility Concerns

### RUBRIC 18
- **CRITERIA**: Must use `google-maps.maps_elevation` tool to check terrain difficulty
- **CATEGORY**: Tool Selection
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: The user has mobility concerns and asked about whether the area is hilly.

### RUBRIC 19
- **CRITERIA**: Elevation check must use the Colosseum coordinates
- **CATEGORY**: Query Construction
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: The user specifically asked about terrain around the Colosseum area.

---

## TURN 7-8: Translate Phrases to Italian

### RUBRIC 20
- **CRITERIA**: Must use `lara-translate.translate` tool for translation
- **CATEGORY**: Tool Selection
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: This is the designated translation tool in the available toolset.

### RUBRIC 21
- **CRITERIA**: Must translate "Where can I buy tickets?" to Italian
- **CATEGORY**: Query Construction
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: The user explicitly requested this phrase to be translated.

### RUBRIC 22
- **CRITERIA**: Must translate "How much does it cost?" to Italian
- **CATEGORY**: Query Construction
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: The user explicitly requested this phrase to be translated.

### RUBRIC 23
- **CRITERIA**: Target language must be "it" (Italian)
- **CATEGORY**: Query Construction
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: The user is visiting Italy and needs Italian translations.

---

## OUTCOME: Final Answer Requirements

### RUBRIC 24
- **CRITERIA**: Response must include when the Colosseum was built (70-80 AD, under Vespasian/Titus)
- **CATEGORY**: Answer Correctness
- **TYPE**: Essential
- **TARGET**: Final Output
- **JUSTIFICATION**: The user explicitly asked about when the Colosseum was built.

### RUBRIC 25
- **CRITERIA**: Response must include the original purpose of the Colosseum (gladiatorial contests, public spectacles)
- **CATEGORY**: Answer Correctness
- **TYPE**: Essential
- **TARGET**: Final Output
- **JUSTIFICATION**: The user explicitly asked what the Colosseum was originally used for.

### RUBRIC 26
- **CRITERIA**: Response must recommend at least 3 restaurants with ratings
- **CATEGORY**: Answer Correctness
- **TYPE**: Essential
- **TARGET**: Final Output
- **JUSTIFICATION**: The user requested "3 highly-rated places" for dining.

### RUBRIC 27
- **CRITERIA**: Response must include walking time from Termini to Colosseum (approximately 20-30 minutes)
- **CATEGORY**: Answer Correctness
- **TYPE**: Essential
- **TARGET**: Final Output
- **JUSTIFICATION**: The user asked how long it would take to walk to the Colosseum.

### RUBRIC 28
- **CRITERIA**: Response must address terrain/elevation for mobility concerns
- **CATEGORY**: Answer Correctness
- **TYPE**: Essential
- **TARGET**: Final Output
- **JUSTIFICATION**: The user has mobility concerns and asked if the area is hilly.

### RUBRIC 29
- **CRITERIA**: Response must include Italian translation of "Where can I buy tickets?"
- **CATEGORY**: Answer Correctness
- **TYPE**: Essential
- **TARGET**: Final Output
- **JUSTIFICATION**: The user requested this specific translation.

### RUBRIC 30
- **CRITERIA**: Response must include Italian translation of "How much does it cost?"
- **CATEGORY**: Answer Correctness
- **TYPE**: Essential
- **TARGET**: Final Output
- **JUSTIFICATION**: The user requested this specific translation.

### RUBRIC 31
- **CRITERIA**: Response must include numbered references to tool outputs
- **CATEGORY**: Answer Correctness
- **TYPE**: Essential
- **TARGET**: Final Output
- **JUSTIFICATION**: References allow verification of claims and demonstrate proper attribution.

### RUBRIC 32
- **CRITERIA**: Response may include the Colosseum's original name (Flavian Amphitheatre)
- **CATEGORY**: Answer Correctness
- **TYPE**: Optional
- **TARGET**: Final Output
- **JUSTIFICATION**: Provides additional historical context but was not explicitly requested.

### RUBRIC 33
- **CRITERIA**: Response may include specific walking route directions (street names)
- **CATEGORY**: Answer Correctness
- **TYPE**: Optional
- **TARGET**: Final Output
- **JUSTIFICATION**: Helpful additional detail but the user only asked for time and general route.

### RUBRIC 34
- **CRITERIA**: Response may include restaurant distances from the Colosseum
- **CATEGORY**: Answer Correctness
- **TYPE**: Optional
- **TARGET**: Final Output
- **JUSTIFICATION**: Useful context for planning but not explicitly requested.

### RUBRIC 35
- **CRITERIA**: Must NOT provide incorrect historical dates for the Colosseum construction
- **CATEGORY**: Answer Correctness
- **TYPE**: Negated
- **TARGET**: Final Output
- **JUSTIFICATION**: Historical accuracy is essential; incorrect dates would misinform the user.

### RUBRIC 36
- **CRITERIA**: Must NOT recommend restaurants outside the 1km radius
- **CATEGORY**: Answer Correctness
- **TYPE**: Negated
- **TARGET**: Final Output
- **JUSTIFICATION**: The user specifically requested restaurants within 1km.

### RUBRIC 37
- **CRITERIA**: Must NOT provide driving directions instead of walking directions
- **CATEGORY**: Answer Correctness
- **TYPE**: Negated
- **TARGET**: Final Output
- **JUSTIFICATION**: The user explicitly asked for walking directions.

---

## GENERAL TASK COMPLETENESS

### RUBRIC 38
- **CRITERIA**: Must complete ALL user requirements: (1) history, (2) restaurants, (3) walking directions, (4) terrain info, (5) translations
- **CATEGORY**: Task Completeness
- **TYPE**: Essential
- **TARGET**: Final Output
- **JUSTIFICATION**: The user made five distinct requests; all must be addressed for task completion.

### RUBRIC 39
- **CRITERIA**: Must use a minimum of 6 distinct tool calls (wikipedia, 2x geocode, places, directions, elevation, 2x translate)
- **CATEGORY**: Task Completeness
- **TYPE**: Essential
- **TARGET**: Process/Reasoning
- **JUSTIFICATION**: The multi-faceted request requires multiple specialized tools to gather all necessary information.
