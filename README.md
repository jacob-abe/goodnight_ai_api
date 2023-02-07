# API for the Goodnight AI App

Be kind, building on an unfamiliar stack and this might not be my greatest work but it should be functional and wanted to build everything publicly

## The architecture: 

### Text+ Image gen flow
* Genre and settings comes from client
* Check if client can generate the story(Rate limit)
* Generate prompt, Store the new story request in user's DB collection and mark status as pending text generation
* Send back story ID back to client

### Story generation cloud function
* Fetch pending story requests from db
* Get prompt from story object, send to open AI to generate story
* Summarise the story for image generation
* Store the summary and text to the story under user, mark status as image generation pending

### Image generation cloud function, runs every 
* Fetch stories with status pending image generation
* Make call to stable diffussion with the summary
* Get back tracking ID and ETA
* Store image tracking ID, eta, image generation timestamp, pending state into user's db.

### Image fetching cloud function, runs every 5 secs
* Check pending stories with an image generation timestamp and status pending image generation. 
* Once ETA is past timestamp, query the fetched image url from Stablediffussion with the tracking ID,
* If the image is ready, store image url in the db story, set state as ready
* If it is not, do nothing

### Story fetch flow:
* From app, query the API every 10 secs, if the cached story ID is a success, get back a boolean with .
* If it is, fetch the story


## Rate limiting the API

* Planning to ask the user to signup with Google Auth, seems like the least barrier to entry
* So google auth will be the AuthN and users once registered, will get saved onto a db collection
* Each user gets one story a day, monthly subscription. Each new user signup gets 1 free story in lifetime
