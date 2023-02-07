# API for the Goodnight AI App

Be kind, building on an unfamiliar stack and this might not be my greatest work but it should be functional and wanted to build everything publicly

## The architecture: 

### Text+ Image gen flow
* Genre and settings comes from client
* Check if client can generate the story(Rate limit)
* Generate prompt, Store the new story request in user's DB collection and mark status as pending text generation
* Send back story ID back to client

### Story generation service runs every x secs
* Fetch pending story requests from db
* Get prompt from story object, send to open AI to generate story
* Summarise the story for image generation
* Store the summary and text to the story under user, mark status as image generation pending

### Image generation service runs every x secs
* Fetch stories with status pending image generation
* Make call to stable diffussion with the summary
* Get back tracking ID and ETA
* Store image url in the db story, set state as ready

### Cleanup service runs every x secs (To keep document sizes down)
* Delete any stories from over 7 days old for every user

### Story fetch flow:
* From app, query the API every 10 secs, if the cached story ID is a success, get back a boolean with .
* If it is, fetch the story


## Rate limiting the API

* Planning to ask the user to signup with Google Auth, seems like the least barrier to entry
* So google auth will be the AuthN and users once registered, will get saved onto a db collection
* Each user gets one story a day, monthly subscription. Each new user signup gets 1 free story in lifetime
