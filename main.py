import discord
from discord.ext import commands
import os
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import AudioDataStream, SpeechSynthesisOutputFormat
import voice_data as vd
import re
import asyncio

# Azure_TTS
# Creates an instance of a speech config with specified subscription key and service region.
AZURE_TTS_TOKEN = os.environ['AZURE_TTS_TOKEN']
speech_key, service_region = AZURE_TTS_TOKEN, "japaneast"
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

# discord
bot = discord.Client()
bot = commands.Bot(command_prefix='!')

# get voice data
voice_module = vd.VoiceModule()
voice_list = vd.get_voice_list_from_local()


@bot.command()
async def h(ctx):
    default_voice_data = voice_module.get_user_data("default")
    default_voice_message = "\nHere is default voice setting:"
    for (key, value) in default_voice_data.voice_setting.items():
        default_voice_message += f"\n       {key} : {value.short_name}"

    string = "How to use this bot:" \
             "\n        Type __`你好__ or __'en Hello__" \
             "\n        Use symbol __`(language key) (text)__" \
             + default_voice_message + \
             "\n" \
             "\nYou can setup your own voice setting." \
             "\nUse command __!set_voice (custom_key) (voice_name)__" \
             "\n                        __!set_default_voice (voice_name)__" \
             "\nAnd __!search (key1) (key2)__ to search usable voice name" \
             "\nExample:" \
             "\n        First, search for a voice __!search korean__" \
             "\n        Then, !set_voice ko ko-KR-SunHiNeural" \
             "\n                !set_default_voice en-GB-LibbyNeural" \
             "\n        And you can use those voices by tying __`ko 안녕__ or __`hello__" \
             "\nVisit here to hear sample audio:" \
             "\nhttps://azure.microsoft.com/en-us/services/cognitive-services/text-to-speech/#features" \
             "\n" \
             "\ntype __!command__ for more command information"
    await ctx.send(string)


@bot.command()
async def command(ctx):
    string = "\nCommand list:" \
             "\n`!leave`" \
             "\nLet bot leave the voice channel" \
             "\n" \
             "\n`!update_voice_list`" \
             "\nUpdate voice list from microsoft official website" \
             "\n" \
             "\n`!show_voice_setting`" \
             "\nShows a list of your voice custom setting" \
             "\n" \
             "\n`!delete_profile`" \
             "\nDelete your profile" \
             "\n" \
             "\n`!delete_voice_setting (key)`" \
             "\nDelete your voice setting with key" \
             "\n" \
             "\n`!set_voice (custom_key) (voice_name)`" \
             "\nSet voice with specific key" \
             "\n" \
             "\n`!set_default_voice (voice_name)`" \
             "\nWhen u didn't define the language, this voice will be chosen" \
             "\n" \
             "\n`!search (key1) (key2)`" \
             "\nSearch for a voice"
    await ctx.send(string)


@bot.command()
async def leave(ctx):
    """
    Let bot leave the voice channel
    :param ctx:
    :return:
    """
    bot_voice_client = next(
        (voice_client for voice_client in bot.voice_clients
         if voice_client.guild == ctx.author.guild), None)
    if bot_voice_client:
        await bot_voice_client.disconnect()
        await ctx.send("Voice channel left")
    else:
        await ctx.send("Not in a voice channel")


@bot.command()
async def update_voice_list(ctx):
    voice_list = vd.get_voice_list_from_microsoft()
    await ctx.send("Done!")


@bot.command()
async def set_voice(ctx, key, voice_name):
    # Replace invalid symbol
    key = re.sub('[<>/|":*]', '', key)
    key = key.replace("\\", " ")

    # Get user voice data
    user_voice_data = voice_module.get_user_data(str(ctx.author.id), False)
    if not user_voice_data.user_id:
        user_voice_data.user_id = str(ctx.author.id)
        user_voice_data.user_name = ctx.author.name

    # Search for voice data
    voice_search_data = voice_module.search(voice_name)
    if len(voice_search_data) == 1:
        # Set voice
        user_voice_data.voice_setting[key] = voice_module.search(voice_name).pop()
        # Save voice data
        voice_module.save_user_data(user_voice_data)
        await ctx.send(f"set_voice: {voice_name}")
    else:
        await ctx.send(f"Wrong voice name! : {voice_name}\n"
                       f"Use !search or visit\n"
                       f"https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support#prebuilt-neural-voices"
                       f"to get correct voice name!")


@bot.command()
async def set_default_voice(ctx, voice_name):
    await set_voice(ctx, "default", voice_name)


@bot.command()
async def search(ctx, search_key1: str, search_key2=""):
    voice_data_search_list = voice_module.search(search_key1, search_key2)

    result = ""
    for voice_data in voice_data_search_list:
        result += f"{voice_data.short_name} {voice_data.gender} {voice_data.locale_name}\n"

    if voice_data_search_list:
        if len(result) > 2000:
            result = result[:1950] + "........\n........."
        await ctx.send(f"Search result:\n{result}")
        # else:
        #     await ctx.send(f"Too many results.\n"
        #                    f"Please change search key and try again!")
    else:
        await ctx.send(f"No data found")


@bot.command()
async def show_voice_setting(ctx):
    # Get user voice data
    user_voice_data = voice_module.get_user_data(str(ctx.author.id), False)
    if not user_voice_data.user_id:
        await ctx.send(f"User profile doesn't exist!")
    else:
        result = "Here is your voice setting\n" \
                 "---------------------------------\n"
        for (key, value) in user_voice_data.voice_setting.items():
            result += f"{key} : {value.short_name}\n"
        result += "---------------------------------\n"
        await ctx.send(f"{result}")


@bot.command()
async def delete_voice_setting(ctx, key):
    # Get user voice data
    user_voice_data = voice_module.get_user_data(str(ctx.author.id), False)
    if not user_voice_data.user_id:
        await ctx.send(f"User profile doesn't exist!")
    else:
        if key in user_voice_data.voice_setting:
            user_voice_data.voice_setting.pop(key)
            voice_module.save_user_data(user_voice_data)
            await ctx.send(f"Setting {key} deleted!")
        else:
            await ctx.send(f"Wrong key!\nPlease check your voice setting by using !show_voice_setting")


@bot.command()
async def delete_profile(ctx):
    # Get user voice data
    user_voice_data = voice_module.get_user_data(str(ctx.author.id), False)
    if not user_voice_data.user_id:
        await ctx.send(f"User profile doesn't exist!")
    else:
        voice_module.delete_user_data(user_voice_data)
        await ctx.send(f"Your profile has been deleted!")


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.event
async def on_message(message: discord.Message):
    # ignore bot message
    if message.author == bot.user:
        return

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    if (message.content.startswith("`") or message.content.startswith("｀")) and len(message.content) > 1:
        # Synthesizes the received text to speech.
        # The synthesized speech is expected to be heard on the speaker with this line executed.

        # Check bot voice channel
        bot_voice_client = await join(message)
        if not bot_voice_client:
            return

        # Replace invalid symbol
        text = re.sub('[<>/|":*]', ' ', message.content[1:])
        text = text.replace("\\", " ")

        if len(text) > 0:
            # Get user voice data
            user_voice_data = voice_module.get_user_data(str(message.author.id))
            default_voice_data = voice_module.get_user_data("default")

            # Check language key
            text_split_list = text.split()
            text_language_key = text.split()[0]
            has_language_key = True
            if len(text_split_list) > 1:
                # Has language key, user profile
                if text_language_key in user_voice_data.voice_setting:
                    language = user_voice_data.voice_setting[text_language_key].locale
                    voice_name = user_voice_data.voice_setting[text_language_key].short_name
                    text = " ".join(text.split()[1:])
                # Has language key, no user profile
                elif text_language_key in default_voice_data.voice_setting:
                    language = default_voice_data.voice_setting[text_language_key].locale
                    voice_name = default_voice_data.voice_setting[text_language_key].short_name
                    text = " ".join(text.split()[1:])
                # No language key
                else:
                    has_language_key = False
            if not has_language_key or not len(text_split_list) > 1:
                text_language_key = "default"
                # Has user default profile
                if text_language_key in user_voice_data.voice_setting:
                    language = user_voice_data.voice_setting[text_language_key].locale
                    voice_name = user_voice_data.voice_setting[text_language_key].short_name
                # No user default profile
                elif text_language_key in default_voice_data.voice_setting:
                    language = default_voice_data.voice_setting[text_language_key].locale
                    voice_name = default_voice_data.voice_setting[text_language_key].short_name

            # Create audio file path
            audio_file_path = f"AudioFile/{voice_name}/{text}.ogg"
            if text == "test_music":
                audio_file_path = "AudioFile/1.m4a"

            # if file doesn't exist, request for it
            if not os.path.exists(audio_file_path):
                speech_config.speech_synthesis_language = language
                speech_config.speech_synthesis_voice_name = voice_name
                speech_config.set_speech_synthesis_output_format(
                    SpeechSynthesisOutputFormat["Ogg16Khz16BitMonoOpus"])

                speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

                result = speech_synthesizer.speak_text_async(text).get()

                # Checks result.
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    print("Speech synthesized to speaker for text [{}]".format(text))
                elif result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = result.cancellation_details
                    print("Speech synthesis canceled: {}".format(cancellation_details.reason))
                    if cancellation_details.reason == speechsdk.CancellationReason.Error:
                        if cancellation_details.error_details:
                            print("Error details: {}".format(cancellation_details.error_details))
                    print("Did you update the subscription info?")

                # Change <?> to ASCII before save
                audio_file_path = audio_file_path.replace('?', '&#63;')

                # Save file to local
                stream = AudioDataStream(result)
                # Check folder path
                audio_folder_path = os.path.dirname(audio_file_path)
                if not os.path.exists(audio_folder_path):
                    # Create a new directory
                    os.makedirs(audio_folder_path)
                stream.save_to_wav_file(audio_file_path)

            # Change <?> to ASCII before load
            audio_file_path = audio_file_path.replace('?', '&#63;')

            audio_source = discord.FFmpegOpusAudio(source=audio_file_path)
            # audio_source = discord.FFmpegPCMAudio(source=audio_file_path)

            while bot_voice_client.is_playing():
                await asyncio.sleep(1)
            bot_voice_client.play(audio_source)

            # Send discord message
            # await message.channel.send(f"{text}")


async def join(ctx):
    """
    Connect/move to voice channel where user is inside
    :param ctx: I have no idea what is this
    :return: bot_voice_client
    """
    # If user in voice channel
    if ctx.author.voice:
        # Get current bot voice channel
        bot_voice_client = next((voice_client for voice_client in bot.voice_clients
                                 if voice_client.guild == ctx.author.guild), None)
        user_voice = ctx.author.voice
        # If bot in a voice channel
        if bot_voice_client:
            # Move to author channel
            if not bot_voice_client.channel == user_voice.channel:
                await bot_voice_client.move_to(user_voice.channel)
        # Or join the author channel
        else:
            bot_voice_client = await user_voice.channel.connect()
    else:
        await ctx.channel.send("You are not in a voice Channel!")
        bot_voice_client = None
    return bot_voice_client


BOT_TOKEN = os.environ['BOT_TOKEN']
bot.run(BOT_TOKEN)
