"""
Grizzy Ai podcast
TODO:
    supports:
        upto latest research --> hookup the internet connection
        adverts -> can be added ( done )
        intro to be used ( done -- watermark )
"""

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

import tempfile
from pydub import AudioSegment
from os import listdir, getenv
import os
from os.path import isfile, join
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
import openai
from moviepy.editor import AudioFileClip, ImageClip
import replicate
import threading
import wget
import json
import spotdl

# from langchain.agents import initialize_agent, Tool
# from langchain.agents import AgentType
# from langchain.tools import BaseTool
# from langchain.llms import OpenAI
# from langchain import LLMMathChain, SerpAPIWrapper
# from langchain.tools import DuckDuckGoSearchResults
# from langchain.tools import WikipediaQueryRun
# from langchain.utilities import WikipediaAPIWrapper
# from langchain.utilities import DuckDuckGoSearchAPIWrapper

# Define your desired data structure.
class ConversationPiece(BaseModel):
    speakers_name: str = Field(description="name of the current speaker")
    speaker_voice: str = Field(description="the voice of the current speaker")
    line: str = Field(description="what the speaker is saying")

class Music(BaseModel):
    theme: str = Field(description="theme of the music to be played")
    position: int = Field(description="position where the music should be played, this should be in relation to the discussion")

class MusicToBePlayed(BaseModel):
    music_theme: str = Field(description="theme of the music to be played")
    mode: str = Field(description="whether the music is a background music or not ( background | foreground )")
    volume_level: float = Field(description="the volume level of the music to be played relative to the expected general volume of the podcast")
    what_percentage: float = Field(description="the percentage of the music to be played")

class Conversation(BaseModel):
    title: str = Field(description="title of the current topic being discussed")
    description: str = Field(description="a single line description of the current topic being discussed")
    music_theme: str = Field(description="the music theme to be played depending on the current topic being discussed")
    music_to_be_played: List[Music] = Field(description="a list of music to be played depending on the current topic being discussed")
    conversation: List[ConversationPiece] = Field(description="a list of the conversation segments within the podcast")

class ConversationWithMergedMusic(BaseModel):
    title: str = Field(description="title of the current topic being discussed")
    description: str = Field(description="a single line description of the current topic being discussed")
    music_theme: str = Field(description="the music theme to be played depending on the current topic being discussed")
    music_to_be_played: List[Music] = Field(description="a list of music to be played depending on the current topic being discussed")
    conversation: List[ConversationPiece | MusicToBePlayed] = Field(description="a list of the conversation segments or music to be played within the podcast")

class Participant(BaseModel):
    name: str = Field(description="name of the participant")
    role: str = Field(description="role of the participant")
    gender: str = Field(description="gender of the participant male or female or other")
    voice: str = Field(description="the voice of the participant")

class SponsorMessage(BaseModel):
    message: str = Field(description="the message to be displayed as a sponsor")

class TextToPodcast:
    def __init__(self) -> None:
        self.chat_model = ChatOpenAI(
            openai_api_key=getenv("OPENAI_API_KEY"), model_name="gpt-3.5-turbo-16k",
            max_tokens=10385,
            temperature=.9
        )
        
        self.parser = PydanticOutputParser(pydantic_object=Conversation)
        self.final_parser = PydanticOutputParser(pydantic_object=ConversationWithMergedMusic)

    def _generate_podcast_script(self, *, name, title, participants: List[Participant], sponsors: List[SponsorMessage] = []) -> ConversationWithMergedMusic:
        sponsors_messages = "\n".join([f"{s.message}" for s in sponsors])

        prompt = PromptTemplate(
            template="Generate a long form podcast script for the following title {title}.The speakers of the podcasts will be {participants}.{sponsors}\n{format_instructions}\n",
            input_variables=["title"],
            partial_variables={
                "format_instructions": self.parser.get_format_instructions(),
                "participants": ", ".join([f"{p.name} ({p.gender}, {p.role} with a voice {p.voice})" for p in participants]),
                "sponsors": f"""\n\n
                Also include these messages from our sponsors. They should be read by either the co-host or the host. Their deliveries should be fluid to the general discussion.

                    SPONSORS MESSAGES
                    ----------------------
                    {sponsors_messages}
                """.strip() if len(sponsors_messages.strip()) > 0 else ""
            }
        )
        
        # work on the script generation to better improve it
        # script was iterated with referrence to :: https://www.ausha.co/blog/podcast-script-templates/
        messages = [
            SystemMessage(content=f"""You are an experienced podcast script writer for the '{name}' podcast. Using your knowledge and experience try your best to to generate the best script for the title supplied by the user. Make the script engaging with wit, sacarsm, crack jokes when necessary or even volunteer experiences or stories the participants might have heard, experienced, been told about or read about that are relevant to the topic under discussion. Be thorough in your discussions, giving each participant equal chances to contribute to the discussion. The script should be mind stimulating, eye opening, fun to listen to and understandable to your audience. Also your podcast participants should pose questions where necessary among themselves or to the listeners. Dont make the podcast too formal. The scripts should have a clear start and ending, do not prematurely end discussions in the middle. The conversations should also be coherent and flow logically. The mood of the title should dictate the mood of the script. Use real names for the participants. Make sure that the script flows. Include the participants reactions e.g [laughs], [sighs], [music], [gasps], [clears throat]. Also add indicators to where music or sounds should be played. Ensure you add music or sounds to the podcast script. For the sounds or music add descriptions to what you want the music to be. use CAPITALIZATION for emphasis of a word. If there is any music to be played make the conversation to flow to it in a clean way.
                          

            Building blocks for a podcast
            ------------------------------------------------
            Intro 👋
                A podcast intro sets the stage for the rest of the show. It is important to get right. Also, audiences are pretty used to host’s reading a script during this part so you really can write it out if you want.

                Here are the sub-sections of an intro in a podcast script template:

            Intro Music 🎵
                If you use different intro music for each episode, you may want to list which song you plan on using. If you are using a mixer and playing the song live during your introduction, you definitely want to have the song chosen ahead of time. Even if you are just going to add the song in post production while editing, it can help to list the intro song in the podcast script just so you have that info in an easy to find place.

            Podcast Title and Tag Line/Short Description 🔦
                This is the first thing you say in your episode, every episode. Write it out for reliability, but after a few episodes even your audience will know it by heart. Listeners love this!

            Roadmap 🗺️
                In terms of podcasts, a roadmap is where you want to list the main points what you are going to cover in that episode. You do not need to go in-depth, just give a brief outline so your audience does not feel like they are flying blind.

            Guest Intro 🤝
                This is the segment meant to hype your listeners up about your guest. List off their relevant achievements, what they are currently doing, and how they tie into what your podcast is about.

                Now is not the time to list their social media handles or do any call to action on their part. That will be in the outro.

            Topics 📂
                You can think of a topic like a section. If you think you only have one topic, break that topic down into more narrow topics.

                For example, let’s say you are going to talk about the fresh water shortage in Hawaii. Break that down into multiple, digestible topics: 1) History of fresh water usage in Hawaii 2) What has caused the current shortage 3) What needs to be done to fix the problem.

                Under each topic, list the main points you want to hit and the supporting data you want to share.

                If you are interviewing a guest, each interview question can act as a topic.

            Sponsor Message 🤑
                Make that money, honey!

                If you have a deal to do a host-read ad for a company, you can put the text you are supposed to read on your podcasts here.

                If you are going to bake in a separately produced advertisement for in post production, just make sure to leave a natural break here.

                Even if you do not have any current promotion contracts, still structure your episode as if you do. In the future you may get a contract and then you can dynamically insert ads into your old episodes.

            Segue ↔️
                Not to be confused with a Segway. You do not need a helmet for this one.

                A segue is the connector between sections. There might need to be a segue between topics, or maybe a segue between a topic and an ad.

                Coming up with a segue on the spot during recording is a great way to stick your foot in your mouth. You may connect two things in a way that is offensive or you may ramble way off course, losing your listeners.

                Consider writing out your segues in full. At the very least, put in a few keywords so you remember how you want to make the transition.

            Recap 🤠
                Like a roadmap, a recap can help your listeners better comprehend the content of your episode and put their brains at ease. It does not need to summarize everything you have talked about, but giving some kind of wrap-up and closure is helpful.

            Outro 👋
                The outro is the long goodbye from you to your audience. But not too long! It is a way for you to send them on their way to feel positive feelings about your show.

                There are a few sub-sections of an outro in a podcast script template:

            Thank Co-Host or Guest 🙌
                Showing your co-host or guest some love and gratitude at the end of the episode helps you build your podcast community. It is a sure way to end the episode on a good note, no matter how tough the material you covered in the episode was. Plus, it is just good manners.

            Call to Action (CTA) 🙏
                This is where you ask your listeners to do something. If you have a guest, usually you list a call to action item or two for them as well.

                Common calls to action are to:
                -------------------------------
                    1. Follow and like the podcast on whatever listening platform that people are using (Apple, Spotify, etc.)
                    2. Share the podcast with friends and on social media
                    3. Visit the podcast’s website and follow their social media pages (including YouTube if you do video episodes)
                    4. Donate to help fund the show
                    5. Sign up for the podcast newsletter
                    6. Register for an in-person event the podcast is putting on
                          
            Next Episode 😎
                Preview what your next episode is going to be about. Let your listeners know when they can expect it to be released. Pump it up a little so they are excited and intrigued.

            Credits 🎞️
                Just like at the end of a movie, you may want to include credits in the outro. It may be something as simple as a quick thank you to someone who gave you the idea of the podcast topic. If you pulled heavily from published resources for you content, you probably want to list them here as well as in your episode notes. And of course if you are lucky enough to have a full team producers, editors, sound designers, etc then here is the place to give them a shout out.
            """),
            HumanMessage(content=prompt.format_prompt(title=title).to_string())
        ]

        result = self.parser.parse(self.chat_model.generate(messages=[messages]).generations[0][0].text)

        # get the result then pass it through another pipeline to merge the music with the conversation
        prompt_clean_pipeline = PromptTemplate(
            template = """Given the podcast script below add sections in the conversation to where the music if any should be played. You should maintain the formatting, only introduce the music segments.\n\n{format_instructions}\n\n\n

                podcast script
                -----------------
                {script}
            
            """.strip(),
            input_variables = [],
            partial_variables = {
                "format_instructions": self.final_parser.get_format_instructions(),
                "script": json.dumps(result.json())
            }
        )

        clean_messages = [
            SystemMessage(
                content="""
                    You are an experienced podcast script editor and programme planner. Using your experience please edit the podcast script with the fragments supplied to produce the best possible script while following the instructions given by the user. Be as professional as possible, fix any grammatical errors you encounter. Also rewrite the participants conversations to allow the co-host or host to smoothly introduce the music to be played if available. Make the music transitions to be as natural as possible, don't break the general flow of the discussion. The conversations should continue with a natural flow even after the music has been played. The participants should acknowledge any music ( background or foreground ) introduced to the conversation. Music MUST be included the conversation flow, be creative with this.
                """.strip()
            ),
            HumanMessage(content=prompt_clean_pipeline.format_prompt().to_string())
        ]

        final_script = self.chat_model.generate(messages=[clean_messages]).generations[0][0].text

        # the final script after the previous check step
        print(final_script)

        return self.final_parser.parse(final_script)
    

    def generate_podcast_resources(self, *, name, title, participants: List[Participant], sponsors: List[SponsorMessage] = []):

        podcast_script = self._generate_podcast_script(
            title=title,
            name=name,
            participants=participants,
            sponsors=sponsors
        )

        with tempfile.TemporaryDirectory() as tmpdirname:
            if not os.path.exists(join(tmpdirname, "fragments")):
                os.makedirs(join(tmpdirname, "fragments"))

            threads = []

            def _run_in_replicate(fragment: int, conversation: ConversationPiece):
                # print(conversation)

                try:
                    # optimize this bit -- make it faster and reliable ( cost friendly )
                    audio = replicate.run(
                        "afiaka87/tortoise-tts:e9658de4b325863c4fcdc12d94bb7c9b54cbfe351b7ca1b36860008172b91c71",
                        input={
                            "text": conversation.line, "voice_a": conversation.speaker_voice.lower(), 
                            "preset": "standard", "seed": 42, "cvvp_amount": 0.9 
                        }
                    )

                    wget.download(audio, join(tmpdirname, "fragments", f"{fragment}.mp3"))
                except Exception as e:
                    print(e)

            for fragment, line in enumerate(podcast_script.conversation):
                if isinstance(line, ConversationPiece):
                    thread = threading.Thread(target=_run_in_replicate, args=(fragment, line))
                    thread.start()

                    threads.append(thread)

                elif isinstance(line, MusicToBePlayed):
                    # search for music fitting the theme ( just combine for now ) ->> forground ->> fade in then can fade out after the what percentage is done
                    # use https://github.com/spotDL/spotify-downloader
                    pass
                else:
                    # this handles transitions -- maybe
                    print(line)
            
            # wait for all the threads to finish
            for thread in threads:
                if thread is not None:
                    thread.join()


            # loop through the files in the fragments folder and combine them
            # have a metadata map for this stuff
            fragments = sorted(
                [join(tmpdirname,"fragments", f) for f in listdir(join(tmpdirname, "fragments")) if isfile(join(tmpdirname, "fragments", f))],
                key=lambda x: int(os.path.basename(x).split(".")[0])
            )

            # watermark
            podcast = AudioSegment.from_file(join(os.getcwd(), "watermarks", "introduction.wav")).append(AudioSegment.silent(duration=500))

            for fragment in map(lambda x: AudioSegment.from_file(x), fragments):
                podcast = podcast.append(fragment)


            if podcast is not None:
                podcast.export(f"{podcast_script.title}.mp3", format="mp3")

                openai.api_key = getenv("OPENAI_API_KEY")

                response = openai.Image.create(
                    prompt=podcast_script.title,
                    n=1,
                    size="1024x1024"
                )

                image_url = response['data'][0]['url']
                # download the image

                audio_clip = AudioFileClip(f"{podcast_script.title}.mp3")
                image_clip = ImageClip(image_url)

                video_clip = image_clip.set_audio(audio_clip)
                video_clip.duration = audio_clip.duration
                video_clip.fps = 30

                video_clip.write_videofile(f"{podcast_script.title}.mp4")


# support generation of content that fits tiktok, youtube and regular podcasts ( we want to support dubbing )
# target for today is to introduce music into the mix

if __name__ == "__main__":
    text_to_podcast = TextToPodcast()

    # text_to_podcast.generate_podcast_resources(
    #     name = "Dingo and the Baby",
    #     title = "greatest wonders of the world",
    #     participants = [
    #         Participant(name="Sharon", role="Host", gender="female", voice="angie"),
    #         Participant(name="Brian", role="Co-host", gender="male", voice="deniro"),
    #         Participant(name="Emma", role="Guest", gender="female", voice="halle"),
    #         Participant(name="John", role="Guest", gender="male", voice="freeman"),
    #     ],
    #     sponsors = [
    #         SponsorMessage(
    #             message="Blueband, the best jam to use"
    #         ),

    #         SponsorMessage(
    #             message="Colgate Total Mouthwash, Stronger, healthier gums.s"
    #         )
    #     ]
    # )

    text_to_podcast._generate_podcast_script(
        name="Dingo and the Baby",
        title="fashion through history",

        participants=[
            Participant(name="Sharon", role="Host", gender="female", voice="angie"),
            Participant(name="Brian", role="Co-host", gender="male", voice="freeman"),
            Participant(name="Dorothy", role="Co-host", gender="female", voice="halle"),
        ],

        sponsors=[
            SponsorMessage(
                message="Blueband, the best jam to use"
            )
        ]
    )