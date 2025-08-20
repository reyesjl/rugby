# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

import json
import openai
import os
from typing import List, Dict

class SequenceGenerator:
    def __init__(self, index_path: str | None = './master_video_index.json'):
        """Initialize generator with a robust index loader.

        Tries in order:
        1) Provided index_path if it exists
        2) animus/data/master_video_index.json
        3) ./master_video_index.json (legacy)
        """
        candidates = []
        if index_path:
            candidates.append(index_path)
        # Prefer new animus location
        candidates.append(os.path.join('animus', 'data', 'master_video_index.json'))
        # Legacy root path
        candidates.append('./master_video_index.json')

        loaded = False
        last_err = None
        for path in candidates:
            try:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        self.video_index = json.load(f)
                        loaded = True
                        break
            except Exception as e:
                last_err = e
                continue

        if not loaded:
            raise FileNotFoundError(
                f"master_video_index.json not found. Tried: {candidates}. Last error: {last_err}"
            )
    
    def search_clips(self, query: str) -> List[Dict]:
        """Find relevant clips based on search query"""
        relevant_clips = []
        
        for video in self.video_index:
            # Search in summary fields
            summary = video['summary']
            searchable_areas = [
                summary.get('summary', ''),
                summary.get('participants', ''),
                ' '.join(summary.get('key_moments', [])),
                video['searchable_text']
            ]
            
            combined_text = ' '.join(searchable_areas).lower()
            if any(term.lower() in combined_text for term in query.split()):
                relevant_clips.append(video)
        
        return relevant_clips
    
    def generate_sequence(self, prompt: str) -> Dict:
        """Generate video sequence based on user prompt"""
        
        # First, get relevant clips
        relevant_clips = self.search_clips(prompt)
        
        # Handle case where no clips are found
        if not relevant_clips:
            return {
                "error": "No relevant clips found for the given prompt",
                "sequence_title": "",
                "total_estimated_duration": "00:00:00",
                "purpose": "",
                "clips": [],
                "editing_notes": []
            }
        
        # Prepare context for GPT
        clips_context = []
        for i, clip in enumerate(relevant_clips[:20]):  # Limit context
            clips_context.append({
                'id': i,
                'file': clip['video_file'],
                'summary': clip['summary']['summary'],
                'tone': clip['summary']['tone'],
                'participants': clip['summary']['participants'],
                'duration': clip['total_duration'],
                'key_segments': [
                    {
                        'text': seg['text'][:100],
                        'start': seg['start_time'],
                        'end': seg['end_time']
                    } for seg in clip['segments'][:3]  # Top 3 segments
                ]
            })
        
        gpt_prompt = f"""
You are a video editor AI specializing in rugby content. Based on the user's request, create a sequence plan using the available clips.

USER REQUEST: "{prompt}"

AVAILABLE CLIPS:
{json.dumps(clips_context, indent=2)}

Create a sequence that fulfills the user's request. Consider:
- Narrative flow and pacing
- Emotional arc (for promotional content)
- Educational progression (for training modules)
- Timing constraints (for reels/social media)

Respond with JSON format:
{{
    "sequence_title": "Generated title",
    "total_estimated_duration": "00:02:30",
    "purpose": "Brief description of the sequence purpose",
    "clips": [
        {{
            "clip_id": 0,
            "file": "folder/file.MPG",
            "start_time": "00:00:15",
            "end_time": "00:00:25",
            "reason": "Why this clip fits here",
            "transition_note": "How to transition to next clip"
        }}
    ],
    "editing_notes": ["Additional guidance for editing"]
}}
"""

        content = None
        try:
            # Check if OpenAI client is configured
            if not hasattr(openai, 'api_key') and not os.getenv('OPENAI_API_KEY'):
                # Fallback: Create a basic sequence without AI
                return self._create_fallback_sequence(prompt, relevant_clips)
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": gpt_prompt}],
                temperature=0.3
            )
            
            # Handle potential None content
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("OpenAI API returned empty response")
            
            # Debug: Print the raw response to understand the issue
            print(f"DEBUG - Raw OpenAI response: {content[:200]}...")
            
            # Try to clean the response if it has markdown formatting
            if content.startswith('```json'):
                content = content.strip('```json').strip('```').strip()
            elif content.startswith('```'):
                content = content.strip('```').strip()
                
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            if content is not None:
                print(f"Raw content: {content}")
            else:
                print("Raw content: Unable to display")
            raise ValueError(f"Failed to parse OpenAI response as JSON: {e}")
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            # Fallback to basic sequence generation
            return self._create_fallback_sequence(prompt, relevant_clips)
    
    def _create_fallback_sequence(self, prompt: str, relevant_clips: List[Dict]) -> Dict:
        """Create a basic sequence when AI is unavailable"""
        # Take first 5 clips and create a simple sequence
        selected_clips = relevant_clips[:5]
        
        clips_list = []
        total_duration = 0
        
        for i, clip in enumerate(selected_clips):
            # Use first segment from each clip
            if clip['segments']:
                segment = clip['segments'][0]
                clips_list.append({
                    "clip_id": i,
                    "file": clip['video_file'],
                    "start_time": segment['start_time'],
                    "end_time": segment['end_time'],
                    "reason": f"Relevant to search query: {prompt}",
                    "transition_note": "Cut to next clip"
                })
                total_duration += segment['duration']
        
        # Format duration
        minutes = int(total_duration // 60)
        seconds = int(total_duration % 60)
        duration_str = f"00:{minutes:02d}:{seconds:02d}"
        
        return {
            "sequence_title": f"Generated Sequence: {prompt}",
            "total_estimated_duration": duration_str,
            "purpose": f"Basic sequence matching: {prompt}",
            "clips": clips_list,
            "editing_notes": ["Basic sequence generated without AI assistance"]
        }

def demo_mode():
    """Run predefined demo sequences"""
    print("\n" + "="*60)
    print("RUGBYCODEX - DEMO MODE")
    print("="*60)
    print("\nGenerating example sequences from your rugby footage...")
    
    generator = SequenceGenerator()
    os.makedirs('./generated_sequences', exist_ok=True)
    
    demo_prompts = {
        "promo_trailer": {
            "prompt": "Produce an uplifting mood video in a trailer style for a promo",
            "description": "Promotional trailer showcasing team energy and highlights"
        },
        "training_modules": {
            "prompt": "Please create 5 modules on the most important topics from training sessions",
            "description": "Educational training modules for skill development"
        },
        "instagram_reel": {
            "prompt": "Create a 30 second reel for Instagram",
            "description": "Quick social media content for engagement"
        },
        "rucking_drills": {
            "prompt": "Find all clips from rucking drills at training",
            "description": "Technical rucking instruction compilation"
        },
        "player_highlights": {
            "prompt": "Find all clips that show Robert tackles",
            "description": "Individual player performance highlights"
        },
        "team_bonding": {
            "prompt": "Create a sequence showing team camaraderie and friendship moments",
            "description": "Team chemistry and social moments"
        }
    }
    
    for i, (name, config) in enumerate(demo_prompts.items(), 1):
        print(f"\n[{i}/{len(demo_prompts)}] {config['description']}")
        print(f"Prompt: '{config['prompt']}'")
        print("Generating... ", end="", flush=True)
        
        try:
            sequence = generator.generate_sequence(config['prompt'])
            
            # Save to file
            filename = f'demo_{name}.json'
            with open(f'./generated_sequences/{filename}', 'w') as f:
                json.dump(sequence, f, indent=2)
            
            # Display summary
            if 'error' not in sequence:
                print("SUCCESS")
                print(f"   Title: {sequence.get('sequence_title', 'Untitled')}")
                print(f"   Duration: {sequence.get('total_estimated_duration', 'Unknown')}")
                print(f"   Clips: {len(sequence.get('clips', []))}")
                print(f"   Saved: {filename}")
            else:
                print("NO CLIPS FOUND")
                print(f"   {sequence['error']}")
                
        except Exception as e:
            print("FAILED")
            print(f"   Error: {e}")
    
    print(f"\nDemo complete! Check ./generated_sequences/ for all files.")
    print("\nTry interactive mode next to create custom sequences!")

def interactive_mode():
    """Run in interactive mode for custom prompts"""
    generator = SequenceGenerator()
    
    print("\n" + "="*60)
    print("RUGBYCODEX - INTERACTIVE MODE")
    print("="*60)
    print("\nCreate custom video sequences with AI!")
    print("Examples:")
    print("  - 'Show me all the best tries from training'")
    print("  - 'Create a motivational video for the team'")
    print("  - 'Find clips of lineout practice'")
    print("  - 'Make a funny blooper reel'")
    
    while True:
        print("\n" + "-"*50)
        
        prompt = input("\nEnter your video request (or 'quit' to exit): ").strip()
        
        if prompt.lower() in ['quit', 'exit', 'q', '']:
            print("Goodbye!")
            break
            
        print(f"\nSearching for clips matching: '{prompt}'")
        print("Generating sequence... ", end="", flush=True)
        
        try:
            sequence = generator.generate_sequence(prompt)
            print("DONE")
            
            if 'error' in sequence:
                print(f"\nERROR: {sequence['error']}")
                print("Try a different search term or check your video library.")
                continue
            
            # Display detailed results
            print(f"\nTitle: {sequence.get('sequence_title', 'Generated Sequence')}")
            print(f"Duration: {sequence.get('total_estimated_duration', 'Unknown')}")
            print(f"Purpose: {sequence.get('purpose', 'Not specified')}")
            
            clips = sequence.get('clips', [])
            print(f"\nSelected {len(clips)} clips:")
            
            for i, clip in enumerate(clips[:5], 1):  # Show first 5
                print(f"   {i}. {clip.get('file', 'Unknown')} ({clip.get('start_time', '00:00')} - {clip.get('end_time', '00:00')})")
                print(f"      Reason: {clip.get('reason', 'No reason provided')}")
            
            if len(clips) > 5:
                print(f"   ... and {len(clips) - 5} more clips")
            
            # Show editing notes
            notes = sequence.get('editing_notes', [])
            if notes:
                print(f"\nEditing Notes:")
                for note in notes:
                    print(f"   - {note}")
            
            # Ask if user wants to save
            save = input(f"\nSave this sequence? (y/n): ").lower().strip()
            if save in ['y', 'yes']:
                default_name = prompt.lower().replace(' ', '_').replace('?', '').replace('!', '')[:20]
                filename = input(f"Enter filename [{default_name}]: ").strip() or default_name
                
                # Ensure .json extension
                if not filename.endswith('.json'):
                    filename += '.json'
                
                os.makedirs('./generated_sequences', exist_ok=True)
                
                with open(f'./generated_sequences/{filename}', 'w') as f:
                    json.dump(sequence, f, indent=2)
                
                print(f"Saved to ./generated_sequences/{filename}")
            
        except Exception as e:
            print("FAILED")
            print(f"\nError: {e}")
            print("Check your API key and try again.")

def main_menu():
    """Main menu for choosing mode"""
    print("\n" + "="*60)
    print("         RUGBYCODEX")
    print("="*60)
    print("\nChoose your mode:")
    print("  [d] Demo mode - See example sequences")
    print("  [i] Interactive mode - Create custom sequences") 
    print("  [q] Quit")
    
    while True:
        choice = input("\nSelect mode [d/i/q]: ").lower().strip()
        
        if choice in ['d', 'demo']:
            demo_mode()
            break
        elif choice in ['i', 'interactive']:
            interactive_mode()
            break
        elif choice in ['q', 'quit', 'exit']:
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 'd', 'i', or 'q'")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
    except FileNotFoundError:
        print("\nError: master_video_index.json not found!")
        print("Run build_searchable_index.py first to create the video index.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")