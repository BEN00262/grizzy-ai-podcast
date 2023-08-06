## brain dump of the grizzy ai ( text to podcast )

### Add this keys to a .env file

```bash:
    OPENAI_API_KEY = "open ai key"
    REPLICATE_API_TOKEN = "replicate key"
```

### open the main.py file and modify

```python:
    if __name__ == "__main__":
        text_to_podcast = TextToPodcast()

        text_to_podcast.generate_podcast_resources(
            name = "Dingo and the Baby", # change this to match your podcast name
            title = "food poisoning", # change this to match the title of the topic you want a podcast to be generated about

            # add your participants ( voices can be angie, deniro, freeman, halle, tom, daniel, emma, geralt, jlaw, tim_reynolds, train_atkins, train_dotrice, train_empire, train_kennard, william )

            participants = [
                Participant(name="Sharon", role="Host", gender="female", voice="angie"),
                Participant(name="Brian", role="Co-host", gender="male", voice="freeman"),
                Participant(name="Dorothy", role="Guest", gender="female", voice="halle"),
            ],

            # change or add sponsors messages in the format as below
            sponsors = [
                SponsorMessage(
                    message="Blueband, the best jam to use"
                )
            ]
        )    

```

### the podcast's mp3 and mp4 files will be generated in the same folder with the `title`.{mp3|mp4} format