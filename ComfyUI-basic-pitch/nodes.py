import os
from typing import Tuple, List, Dict, Any
from basic_pitch.inference import predict
from midiutil import MIDIFile

class AudioToMidi:
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "required": {
                "audio_path": ("STRING", {
                    "multiline": False,
                    "placeholder": "Path to audio file"
                }),
            },
            "optional": {
                "onset_threshold": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01
                }),
                "frame_threshold": ("FLOAT", {
                    "default": 0.3,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01
                }),
            }
        }

    RETURN_TYPES = ("MIDI_DATA",)
    FUNCTION = "convert_audio_to_midi"
    CATEGORY = "basic-pitch"

    def convert_audio_to_midi(self, 
                            audio_path: str, 
                            onset_threshold: float = 0.5, 
                            frame_threshold: float = 0.3) -> Tuple[List]:
        if not os.path.exists(audio_path):
            raise ValueError(f"Audio file not found: {audio_path}")

        try:
            # Perform pitch estimation with the correct parameters
            model_output, midi_data, note_events = predict(
                audio_path,
                onset_threshold=onset_threshold,
                frame_threshold=frame_threshold
            )
            
            # Process the MIDI data from the PrettyMIDI object
            processed_midi_data = []
            
            # Iterate through all instruments
            for instrument in midi_data.instruments:
                # Get all notes from the instrument
                for note in instrument.notes:
                    processed_midi_data.append((
                        int(note.pitch),
                        float(note.start),
                        float(note.end),
                        int(note.velocity)
                    ))
            
            # Sort by start time
            processed_midi_data.sort(key=lambda x: x[1])
            
            return (processed_midi_data,)

        except Exception as e:
            raise RuntimeError(f"Error during audio-to-MIDI conversion: {str(e)}")


class SaveMidi:
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "required": {
                "midi_data": ("MIDI_DATA",),
                "file_name": ("STRING", {
                    "default": "output.mid",
                    "multiline": False,
                    "placeholder": "Output file name"
                }),
                "output_path": ("STRING", {
                    "default": "D:\\OLD_ComfyUI_windows_portable\\ComfyUI\\output\\midi",
                    "multiline": False,
                    "placeholder": "Output directory path"
                }),
                "tempo": ("INT", {
                    "default": 120,
                    "min": 20,
                    "max": 300,
                    "step": 1
                }),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_midi"
    CATEGORY = "basic-pitch"
    OUTPUT_NODE = True

    def save_midi(self, midi_data: List, file_name: str, output_path: str, tempo: int = 120) -> Tuple:
        if not midi_data:
            raise ValueError("No MIDI data provided")

        # Create a MIDI file
        midi = MIDIFile(1)  # One track
        track = 0
        time = 0
        channel = 0

        # Add track name and tempo
        midi.addTrackName(track, time, "Track 1")
        midi.addTempo(track, time, tempo)

        # Add notes
        for note in midi_data:
            if len(note) != 4:
                continue  # Skip invalid note data
                
            pitch, start_time, end_time, velocity = note
            duration = end_time - start_time
            
            # Ensure values are within valid MIDI ranges
            pitch = max(0, min(127, int(pitch)))
            velocity = max(0, min(127, int(velocity)))
            
            midi.addNote(
                track=track,
                channel=channel,
                pitch=pitch,
                time=start_time,
                duration=duration,
                volume=velocity
            )

        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Save the MIDI file
        output_file = os.path.join(output_path, file_name)
        try:
            with open(output_file, "wb") as f:
                midi.writeFile(f)
        except Exception as e:
            raise RuntimeError(f"Error saving MIDI file: {str(e)}")

        return ()


NODE_CLASS_MAPPINGS = {
    "AudioToMidi": AudioToMidi,
    "SaveMidi": SaveMidi,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AudioToMidi": "Audio to MIDI Converter",
    "SaveMidi": "Save MIDI File",
}