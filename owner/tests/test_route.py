from owner.ask_bot import route


def test_typed_commands_and_buttons():
    cases = {
        "show me my dog": "check", "What is my dog doing?": "check", "is he calm?": "check",
        "how is bruno": "check", "hi": "check",
        "calm voice": "voice", "play my voice": "voice", "🔊 Voice": "voice", "talk to him": "voice",
        "give treat": "treat", "🦴 Treat": "treat", "give him a snack": "treat",
        "roll the ball": "ball", "🎾 Ball": "ball", "ball rolling": "ball",
        "📹 Play my video": "video", "play video": "video",
        "/start": "help",
    }
    for text, expected in cases.items():
        assert route(text) == expected, text
