# API for the Goodnight AI App

Be kind, building on an unfamiliar stack and this might not be my greatest work but it should be functional and wanted to build everything publicly

## The architecture is simple. 

* The prompt and genre along with other params are sent from the mobile/web app
* A prompt is built to generate a story, passed to OpenAI and gets back generated text
* The generated text is summarised and important subject fed back to client along with the generated text
* Images are generated from the summary/important subject, from OpenAI
* Text and images are 2 endpoints, still debating if its better to make it one. Since the image should be dependent on the generated story

## Rate limiting the API

* Planning to ask the user to signup with Google Auth, seems like the least barrier to entry
* So google auth will be the AuthN and users once registered, will get saved onto a Mongo collection
* Each user gets a free tier Goodnight token a month. Beyond that, they purchase Goodnight tokens.
* They can generate the text if they have tokens available, can be a monthly subscription.
