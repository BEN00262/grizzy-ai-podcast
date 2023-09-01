## brain dump of the grizzy ai ( text to podcast ) 
### listen to some generated content at [https://grizzy-ai.transistor.fm/](https://grizzy-ai.transistor.fm/)

### Add this keys to a .env file

```bash
    OPENAI_API_KEY = "open ai key"
    SPEECH_KEY = "azure speech key"
    SPEECH_REGION = "azure speech region"
```

### open the main.py file and modify

```python
    if __name__ == "__main__":
        text_to_podcast = TextToPodcast()

        text_to_podcast.generate_podcast_resources(
            name = "Dingo and the Baby", # change this to match your podcast name
            title = "food poisoning", # change this to match the title of the topic you want a podcast to be generated about

            """
                supported voices
                -------------------
                    en-GB-SoniaNeural (Female)
                    en-GB-RyanNeural (Male)
                    en-GB-LibbyNeural (Female)
                    en-GB-AbbiNeural (Female)
                    en-GB-AlfieNeural (Male)
                    en-GB-BellaNeural (Female)
                    en-GB-ElliotNeural (Male)
                    en-GB-EthanNeural (Male)
                    en-GB-HollieNeural (Female)
                    en-GB-MaisieNeural (Female, Child)
                    en-GB-NoahNeural (Male)
                    en-GB-OliverNeural (Male)
                    en-GB-OliviaNeural (Female)
                    en-GB-ThomasNeural (Male)
            """

            participants = [
                Participant(name="Sharon", role="Host", gender="female", voice="en-GB-SoniaNeural"),
                Participant(name="Brian", role="Co-host", gender="male", voice="en-GB-RyanNeural"),
                Participant(name="Dorothy", role="Guest", gender="female", voice="en-GB-BellaNeural"),
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