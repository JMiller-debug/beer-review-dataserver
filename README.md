# Todo

## Database/dataserver
- Add review table to the database to hold user reviews, should include score
  and have a foreign key that references the beer and free text field. User name
  of the person who left the review as well. Date created as well, maybe a last updated if they edit the review
- Change score to be average of all the reviews 
- Add endpoint that returns recent reviews, top reviews, worse reviews
- Add location field to the beer company to say where they are located/from

## Website
- Change dashboard to showcase Breweries as well (maybe)
- Change dashboard to show new beers, recently updated beers or top scoring
  beers (maybe hot beers to, recently updated high scoring beers)
- Add page to post beers
    - Features:
        - Fuzzy Search Companies in the database based on name
        - Create beer + post review
        - Add image for the beer (Big change Later)
- Add page to add new Breweries to the database
    - Admin restricted (Just because)
- Add ability to leave reviews under beers
    - Needs the ability to support pagination of the reviews
- Add page to search beers
- Add page to search companies
    - View newest beers, top-rated beers, a lineup, top reviews about some of
      their beers
