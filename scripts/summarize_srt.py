import os
from openai import OpenAI
import json

# Directory with SRT files
TRANSCRIPTS_DIR = "./transcripts"
OUTPUT_DIR = "./summaries"

# Get your API key from environment or hardcode here (not recommended)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_srt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def call_gpt_to_summarize(srt_text):
    prompt = f"""
            You are a storytelling assistant trained to analyze raw video transcripts from a handheld camcorder. These videos include rugby training, matches, post-game hangouts, community events, and casual scenes. Your job is to summarize the essence of each clip in 3–6 sentences, with an eye toward creating a visual documentary archive. For each video:

            1. Describe the setting and who is speaking or present.
            2. Capture the main activity, story, or dialogue.
            3. Highlight anything memorable, funny, emotional, or culturally significant.
            4. If the clip is coaching, include key lessons or advice.
            5. If it's casual or scenic, highlight the vibe or energy.

            Avoid filler and repetition. Maintain a respectful and observant tone. Assume the final output may be used for organizing footage, editing videos, or archiving history for a future film or documentary.

            Please provide your response as a JSON object with the following structure:
            {{
                "summary": "Your 3-6 sentence summary here",
                "setting": "Brief description of the setting",
                "participants": "Who is present or speaking",
                "key_moments": ["List of notable moments or quotes"],
                "tone": "Overall mood/energy of the clip"
            }}

SRT Transcript:
{srt_text[:6000]}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Much cheaper alternative to gpt-4
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    
    content = response.choices[0].message.content
    if content is not None:
        print(f"GPT Response: {content[:200]}...")  # Debug: show first 200 chars
        
        # Clean the response - remove markdown code blocks if present
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]  # Remove ```json
        if content.startswith('```'):
            content = content[3:]   # Remove just ```
        if content.endswith('```'):
            content = content[:-3]  # Remove closing ```
        content = content.strip()
        
    else:
        print("GPT Response: None")
        content = "{}"
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Cleaned response: {content}")
        # Fallback: create a basic structure
        return {
            "summary": content[:500] if content else "No summary available",
            "setting": "Unknown",
            "participants": "Unknown", 
            "key_moments": [],
            "tone": "Unknown"
        }

def process_srt_files(max_files=None):
    processed_count = 0
    for root, _, files in os.walk(TRANSCRIPTS_DIR):
        for file in files:
            if not file.endswith(".srt"):
                continue

            srt_path = os.path.join(root, file)
            folder = os.path.basename(os.path.dirname(srt_path))
            base = os.path.splitext(file)[0]
            
            # Create folder structure in summaries directory
            output_folder = os.path.join(OUTPUT_DIR, folder)
            os.makedirs(output_folder, exist_ok=True)
            output_file = os.path.join(output_folder, f"{base}.json")

            if os.path.exists(output_file):
                print(f"Skipping existing: {output_file}")
                continue

            print(f"Processing: {srt_path}")
            srt_text = read_srt(srt_path)
            try:
                result = call_gpt_to_summarize(srt_text)
                result["filename"] = file
                result["folder"] = folder

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                print(f"Saved: {output_file}")
                processed_count += 1
            except Exception as e:
                print(f"Failed on {file}: {e}")
                
    print(f"Completed processing {processed_count} files total.")

if __name__ == "__main__":
    # Process all files - no limit
    process_srt_files()  # Removed max_files parameter to process all videos
