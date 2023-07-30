"""
PodcastAI
    supports:
        upto latest research
        adverts -> can be added
        intro to be used
"""


from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

import pyttsx3
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

# Define your desired data structure.
class ConversationPiece(BaseModel):
    speakers_name: str = Field(description="name of the current speaker")
    speaker_voice: int = Field(description="the voice of the current speaker choose between 1 and 0. 1 being a female voice and 0 being a male voice")
    line: str = Field(description="what the speaker is saying")
    
class Conversation(BaseModel):
    title: str = Field(description="title of the current topic being discussed")
    description: str = Field(description="a single line description of the current topic being discussed")
    conversation: List[ConversationPiece] = Field(description="a list of the conversation segments")


class TextToPodcast:
    def __init__(self) -> None:
        self.chat_model = ChatOpenAI(
            openai_api_key=getenv("OPENAI_API_KEY"), model_name="gpt-3.5-turbo-16k"
        )
        
        self.parser = PydanticOutputParser(pydantic_object=Conversation)
        self.engine = pyttsx3.init()

    def _generate_podcast_script(self, title) -> Conversation:
        prompt = PromptTemplate(
            template="Generate a long form podcast script for the following title {title}.\n{format_instructions}\n",
            input_variables=["title"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        messages = [
            SystemMessage(content="""You are an experienced podcast script writer. Using your knowledge and experience try your best to to generate the best script for the title supplied by the user. Make the script engaging with wit, sacarsm, crack jokes when necessary or even volunteer experiences or stories the participants might have heard, experienced, been told about or read about that are relevant to the topic under discussion. Be thorough in your discussions, giving each participant equal chances to contribute to the discussion. The script should be mind stimulating, eye opening, fun to listen to and understandable to your audience. Also your podcast participants should pose questions where necessary among themselves or to the listeners. Dont make the podcast too formal. The scripts should have a clear start and ending, do not prematurely end discussions in the middle. The conversations should also be coherent and flow logically. The mood of the title should dictate the mood of the script. Use real names for the participants. Make sure that the script flows.
            
                          
            ============START OF RULES================
                          
            At a minimum you want the following scripted:
            ------------------------------------------------
                Introduction to you/podcast

                Introduction to topic and guests

                Questions (you can deviate from these)

                Call to action

                Outro (closing)

            
            Dos and don’ts for podcast scripts:
            ------------------------------------------------
                DO write in a conversational tone and include abbreviations

                DON’T write as if you’re writing an essay 

                DO write in your own words and tone of voice. Does it sound like you when you’re chatting with friends?

                DON’T use overly complicated language (unless it’s a technical podcast aimed at an audience who are knowledgeable about the subject matter)

                DON’T write everything word-for-word. It’s nearly impossible to sound natural when you do this

                DO leave room to ad-lib. You’ll only get a feel for how much scripting vs ad-libbing you need once you get started
                          
            =============END OF RULES============
                          

            sample podcast script to use for reference
            ==================================================
            Series intro:
                          
                Hello and welcome to (podcast name). The podcast series where we talk about
                (topic). I’m (name of host) and I’m with (name of co-host). 

                Episode intro:
                            
                In today’s episode, we’ll be talking about (episode topic - why should listeners
                care). We’re/I’m joined by (guest name, guest job title) who will be sharing their
                (thoughts/experience).
                Welcome to guest:
                Hello and welcome.
                          
            Talking points
                          
                • Talking point 1 (introduction, overview of subject why it’s important)
                • Link to talking point 2
                • Talking point 2 (introduce with key facts/research)
                • Link to talking point 3
                • Talking point 3 (introduce with key facts/research)
                • Key takeaways/looking to the future from guest
         
            Outro:
                          
                Thanks to (name of guest here). Recap of what was spoken about and what you
                want your audience to go away with.
                          
            Call to action:
                          
                (this can appear earlier on if there’s a natural point to have it mid-episode): 

                Please rate, review and subscribe to or follow the podcast on Apple, Spotify or
                wherever you get your podcasts.
            Final words:
                I’m (your name). Thanks for listening.
            """),
            HumanMessage(content=prompt.format_prompt(title=title).to_string())
        ]

        result = self.chat_model.generate(messages=[messages])

        return self.parser.parse(result.generations[0][0].text)
    

    def generate_podcast_resources(self, title):
        voices = self.engine.getProperty('voices')

        podcast_script = self._generate_podcast_script(title=title)

        with tempfile.TemporaryDirectory() as tmpdirname:
            if not os.path.exists(join(tmpdirname, "fragments")):
                os.makedirs(join(tmpdirname, "fragments"))

            for fragment, line in enumerate(podcast_script.conversation):
                self.engine.setProperty('voice', voices[line.speaker_voice].id)
                self.engine.save_to_file(line.line, join(tmpdirname, "fragments", f"fragment_{fragment}.mp3"))
                self.engine.runAndWait()

            self.engine.stop()

            # loop through the files in the fragments folder and combine them
            fragments = [join(tmpdirname,"fragments", f) for f in listdir(join(tmpdirname, "fragments")) if isfile(join(tmpdirname, "fragments", f))]
            fragments.sort()

            podcast = None

            for fragment in map(lambda x: AudioSegment.from_file(x), fragments):
                if podcast is None:
                    podcast = fragment
                    continue

                podcast = podcast.append(fragment)


            if podcast is not None:
                podcast.export(f"{podcast_script.title}.mp3", format="mp3")
                # generate an image of the podcast and overlay it with a description and the title then combine the 
                # audio and image to make a video
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
if __name__ == "__main__":
    text_to_podcast = TextToPodcast()
    text_to_podcast.generate_podcast_resources("crazy dating stories and experiences")