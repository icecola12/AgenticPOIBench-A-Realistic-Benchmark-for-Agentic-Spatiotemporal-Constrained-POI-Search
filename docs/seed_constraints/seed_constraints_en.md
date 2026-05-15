
|   |   |   |
|---|---|---|
|**Constraint**|**Description**|**Example**|
|**Spatial Constraints**|||
|Maximum euclidean distance constraint (to reference point)|Straight-line distance from POI to reference point does not exceed a specified distance.|Coffee shops near me within 2km.|
|Nearby POI existence constraint|Specified POI types exist within a specified distance around the POI.|Find a hotel near a subway station for me.|
|Geographic region membership constraint|POI is located within a specified administrative region.|Find a shopping mall in Administrative Region X.|
|Minimum/nearest distance constraint (to reference point)|POI has the shortest straight-line distance to the reference point.|Find the nearest bar.|
|Maximum walking distance constraint (from origin)|Maximum walking distance limit from POI to the origin.|Find me a park within a 1.5km walk.|
|Proximity to public transit station (walking distance)|Public transit is within walking distance of the POI.|Find a laundromat within a 300-meter walk of a bus station.|
|Direction-and-distance joint constraint|POI is located in a specified direction from the reference point and within a specified distance limit.|Find a KTV within 2km to my northeast.|
|Multi-condition spatial composition constraint|POI simultaneously satisfies multiple spatial constraints.|My friend's at location_A. Find me a hot pot place within 5km of me and 3km of him.|
|Mode-based reasonable distance constraint|Reasonable distance between POI and the current location.|Nearby parks accessible by bike.|
|Proximity to public transit station (euclidean distance)|A public transit station exists within a straight-line distance of the POI.|Find a study room with a metro within 300 meters.|
|Non-proximity constraint|POI is not located near other specified locations.|Could you help me find a parking lot that is a bit further away from the location_A?|
|Maximum driving distance constraint (from origin)|Maximum driving distance limit from POI to the reference point.|I need a gas station within a 20km drive.|
|Maximum distance constraint to a specific bus stop|Maximum distance limit from POI to a specified bus stop.|Can you help me find an ATM within 2km of location_A?|
|En-route waypoint proximity constraint|Route to the POI passes through another specified point.|ATMs along the route through location_A.|
|Maximum cycling distance constraint (from origin)|Maximum cycling distance limit from POI to the reference point.|Find a public restroom within 1.5km by bike.|
|En-route nearby POI constraint|Specified POI types exist around waypoints on the route from POI to the reference point.|Esports lounges along the way to location_A, near a convenience store.|
|Round-trip distance constraint|Round-trip distance from POI to the reference point does not exceed a specified value.|Looking for a picnic spot within a 20km round trip drive.|
|Distance-based sorting constraint|POIs are sorted by distance from nearest to farthest relative to the reference point.|Find parking near me, sorted by distance.|
|**Temporal Constraints**|||
|Minimum travel time optimization constraint|Find the quickest-accessible POI.|Find the fastest hospital to get to.|
|Maximum walking time constraint (from departure location)|Maximum walking time limit from the POI to the reference point.|Find a public restroom within a 20-minute walk.|
|Maximum driving time constraint (from departure location)|Maximum driving time limit from the POI to the reference point.|Find a hospital within a 10-minute drive.|
|Dual-origin travel time difference constraint|The difference in arrival times from the POI to two reference points is less than a specified duration.|Find an internet cafe that's a similar distance for both me and my friend at location_A, keep the travel time difference under 10 minutes.|
|Proximity to transit hub travel time constraint|The arrival time from the POI to a transit hub is less than a specified duration.|Find a restaurant within a 20-minute commute to a subway station.|
|Via-Point Total Travel Time Constraint|The total additional detour time incurred by adding a waypoint is less than a specified duration.|Find a museum with a detour to location_A that's under 40 minutes.|
|Maximum cycling time constraint (from departure location)|Maximum cycling time limit from the POI to the reference point.|Find a study room within a 20-minute bike ride.|
|Round-trip feasibility constraint|The POI supports round-trip travel within a specified time limit.|Find a supermarket within a 20-minute round trip.|
|Maximum driving time to major transportation hub constraint|Maximum travel time limit from the POI to a specific transit hub.|Find a cafe within a 1-hour drive of location_A.|
|Detour time overhead constraint|The detour time incurred by passing through the POI to the final destination is less than the direct travel time.|Find a post office on the way to location_A that adds less than 20 minutes to the total trip.|
|**Semantic Constraints**|||
|Facility Features|POI Functionality.|I want to get a haircut.|
|Ratings and Quality|POI Rating and Quality.|Find me a coffee shop with a 4.2+ rating.|
|Venue Type|POI Type.|Find me a charging station.|
|Price and Cost|POI Price and Average Spend per Person.|Looking for a Sichuan spot under 80 yuan per person.|
|Hours and Availability|POI Operating Hours.|Find me a 24-hour convenience store.|
