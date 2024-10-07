import os
import re
import PyPDF2
import google.generativeai as genai
from moviepy.editor import ImageClip, VideoFileClip, concatenate_videoclips,AudioFileClip
from concurrent.futures import ThreadPoolExecutor
from moviepy.video.fx.all import speedx
from moviepy.video.fx.all import fadein, fadeout

# Configure the Gemini API
genai.configure(api_key="AIzaSyAcpkdxOkgN0iPb_tgq3ZV_pFVpotx_-gA")

# Create the model configuration for Gemini
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Function to clean text (remove special characters, extra spaces, etc.)
def clean_text(text):
    cleaned_text = re.sub(r'[#*]', '', text)  # Remove unwanted characters like # and *
    cleaned_text = ' '.join(cleaned_text.split())  # Remove multiple spaces
    return cleaned_text

# Function to extract keywords from image filenames
def extract_keywords_from_images(image_folder):
    keywords = set()  # Use a set to avoid duplicate keywords
    try:
        # Iterate through all files in the image folder
        for file_name in os.listdir(image_folder):
            if file_name.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):  # Check for image files
                # Remove the file extension and split by underscore
                name_without_extension = os.path.splitext(file_name)[0]
                keyword_parts = name_without_extension.split('_')
                # Add each part as a keyword
                keywords.update(keyword_parts)
    except Exception as e:
        print(f"Error reading files from {image_folder}: {e}")

    return list(keywords)  # Convert the set back to a list for the result

# Function to extract keywords using Gemini AI
def extract_keywords_gemini(text, top_n=8):
    try:
        # Generate a prompt asking Gemini to extract keywords from the text
        prompt = f"{text} Extract the top {top_n} simple and most common keywords without any symbols, descriptions,reactions(like HAA HAA,W W) and also arrange in manner of story "
        
        # Use Gemini AI to process the request
        response = model.generate_content(prompt)

        # Assuming the response from Gemini is plain text with one keyword per line
        keywords = response.text.splitlines()

        # Limit to the top N keywords (in case Gemini returns more)
        return keywords[:top_n]
    except Exception as e:
        print(f"Error extracting keywords with Gemini: {e}")
        return []

# Function to read a text file and return its content
def read_text_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""


# Function to save the combined extracted keywords to a new file
def save_combined_keywords_to_file(keywords, output_folder, base_filename):
    try:
        # Define the path where the keywords will be saved
        keywords_output_path = os.path.join(output_folder, f"{base_filename}_combined_keywords.txt")
        # Write the keywords to the file
        with open(keywords_output_path, 'w', encoding='utf-8') as file:
            file.write('\n'.join(keywords))  # Join the keywords with newlines
        print(f"Combined keywords saved to {keywords_output_path}")
    except Exception as e:
        print(f"Error saving combined keywords: {e}")

def process_keywords(keywords):
    cleaned_keywords = []
    for keyword in keywords:
        cleaned_keyword = re.sub(r"^\d+\.\s*", "", keyword).strip()
        if cleaned_keyword:  # Ignore empty strings
            cleaned_keywords.append(cleaned_keyword)
    return cleaned_keywords

#effects 
def apply_pan_effect(clip, pan_duration, direction="right", pan_speed=15):
    width, height = clip.size

    def pan_frame(get_frame, t):
        frame = get_frame(t)
        x_move = int(pan_speed * t)
        if direction == "right":
            return frame[:, x_move:min(width, x_move + width), :]  # Pan right
        elif direction == "left":
            return frame[:, max(0, width - x_move):width, :]  # Pan left
        return frame

    return clip.fl(pan_frame).set_duration(pan_duration)


def is_valid_clip(clip):
    """ Check if a clip is valid (non-empty and has duration). """
    return clip is not None and clip.duration > 0

def generate_combined_video_from_keywords(keywords, image_folder, output_folder, audio_file, base_file,target_size=(1280, 720)):
    clips = []
    used_images = set()  # To track used images

    # Process the keywords to remove empty strings and clean formatting
    keywords = process_keywords(keywords)

    # Load the audio file and get its duration
    if not os.path.exists(audio_file):
        print(f"Audio file {audio_file} not found.")
        return None

    try:
        audio = AudioFileClip(audio_file)
        audio_duration = audio.duration
    except Exception as e:
        print(f"Error loading audio file: {e}")
        return None

    # Calculate the duration for each image
    num_keywords = len(keywords)
    if num_keywords == 0:
        print("No keywords provided.")
        return None

    clip_duration = audio_duration / min(num_keywords, audio_duration // 5)  # Ensure we use just enough keywords
    total_video_duration = 0  # To track the total duration of video clips
    print(f"Each clip will have a duration of {clip_duration} seconds.")

    for keyword in keywords:
        if total_video_duration >= audio_duration:
            print("Reached the audio duration limit. Skipping remaining keywords.")
            break  # Stop if the total video duration exceeds the audio duration

        print(f"Looking for images for keyword: {keyword}")  # Debugging output
        image_found = False

        for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            image_filename = f"{keyword}{ext}"
            image_path = os.path.join(image_folder, image_filename)

            if os.path.exists(image_path) and image_path not in used_images:
                try:
                    if ext == '.gif':
                        gif_clip = VideoFileClip(image_path)
                        if gif_clip.duration > 0:
                            slow_gif_clip = speedx(gif_clip, factor=0.5)  # Slow down the GIF
                            clip = slow_gif_clip.resize(target_size).subclip(0, min(clip_duration, slow_gif_clip.duration))
                        else:
                            continue
                    else:
                        # If remaining time is less than the calculated clip duration, adjust the clip duration
                        remaining_time = audio_duration - total_video_duration
                        current_clip_duration = min(clip_duration, remaining_time)
                        
                        clip = ImageClip(image_path).set_duration(current_clip_duration).resize(target_size)
                        clip = clip.resize(lambda t: 1 + 0.1 * t)  # Zoom in over time
                        clip = apply_pan_effect(clip, pan_duration=current_clip_duration, direction="right")  # Pan right
                        clip = fadeout(clip, 1)

                    # Validate the clip before appending
                    if is_valid_clip(clip):
                        clips.append(clip)
                        used_images.add(image_path)
                        image_found = True
                        total_video_duration += current_clip_duration  # Update total video duration
                        break  # Exit loop after finding the first valid image
                    else:
                        print(f"Invalid clip generated for image: {image_path}")
                except Exception as e:
                    print(f"Error processing image {image_path}: {e}")

        if not image_found:
            print(f"Image not found for keyword: {keyword}")

    print(f"Number of clips generated: {len(clips)}")

    # Check if there are clips before concatenating
    if len(clips) == 0:
        print("No clips were generated. Ensure images are available and valid.")
        return None

    # Concatenate the video clips
    try:
        # Filter valid clips only
        valid_clips = [clip for clip in clips if is_valid_clip(clip)]
        
        if not valid_clips:
            print("No valid clips available for concatenation.")
            return None
        print(audio)
        final_video = concatenate_videoclips(valid_clips, method="compose")
        final_video = final_video.set_audio(audio)  # Add the audio to the video
        video_output_path = os.path.join(output_folder, f"{base_file}_video_with_audio.mp4")
        final_video.write_videofile(video_output_path, fps=24)
        final_video.close()  # Close video resources
        audio.close()  # Close audio resources

        print(f"Video generated successfully: {video_output_path}")
        return video_output_path
    except Exception as e:
        print(f"Error during video generation: {e}")
        return None

    
#merge audio file
def merge_videos_with_audio(video_paths, output_folder, audio_folder):
    try:
        # Merge video clips
        video_clips = [VideoFileClip(path) for path in video_paths]
        final_video = concatenate_videoclips(video_clips)
        final_output_path = os.path.join(output_folder, "final_merged_video.mp4")

        # Find the audio file with 'full_audio.mp3' suffix
        audio_file = None
        for file_name in os.listdir(audio_folder):
            if file_name.endswith("full_audio.mp3"):
                audio_file = os.path.join(audio_folder, file_name)
                break

        if audio_file:
            # Load audio and set it to the video
            final_audio = AudioFileClip(audio_file)
            final_video = final_video.set_audio(final_audio)

        # Write the final video with audio, explicitly setting FPS
        final_video.write_videofile(final_output_path, fps=24, codec='libx264')
        print(f"Final merged video with audio saved to {final_output_path}")
    except Exception as e:
        print(f"Error merging videos with audio: {e}")

# Function to process text files and images for keyword extraction
def process_files_for_keywords(text_folder, image_folder, output_folder,base_file):
    combined_keywords = set()  # Use a set to avoid duplicates
   
    # Process text files for keywords
    for text_file in os.listdir(text_folder):
        if text_file.endswith(".txt"):
            text_file_path = os.path.join(text_folder, text_file)
            raw_text = read_text_file(text_file_path)
            if raw_text:
                cleaned_text = clean_text(raw_text)
                keywords_from_text = extract_keywords_gemini(cleaned_text, top_n=10)  # Extract keywords from text
                combined_keywords.update(keywords_from_text)

    # Extract keywords from image filenames
    keywords_from_images = extract_keywords_from_images(image_folder)
    combined_keywords.update(keywords_from_images)

    # Save the combined keywords to a new file
   
    save_combined_keywords_to_file(list(combined_keywords), output_folder, os.path.splitext(text_file)[0])
    video_name = base_file.replace("_full_audio.mp3", '')
    video_path = generate_combined_video_from_keywords(list(combined_keywords), image_folder, output_folder,text_folder+"/"+base_file,video_name)

    # Merge all videos into one final video
    if video_path:
        merge_videos_with_audio(video_path, output_folder,text_folder)
    else:
        print("No videos were generated to merge.")



# Example usage
# if __name__ == "__main__":
#     # Folder with input paragraph text files
#     text_folder = "D:\\Projects ALL\\AI Based\\P-Dio\\PRECEPTION\\output_txt"
#     # Folder with images
#     image_folder = "D:\\Projects ALL\\AI Based\\P-Dio\\PRECEPTION\\dataset\\english"
#     # Folder where the keywords and videos will be saved
#     output_folder = "D:\\Projects ALL\\AI Based\\P-Dio\\PRECEPTION\\Keywords"

#     # Process text files and images to generate combined keywords and videos
#     process_files_for_keywords(text_folder, image_folder, output_folder,"geah103_full_audio.mp3")

#     print("Keyword extraction, video generation, and merging complete.")  