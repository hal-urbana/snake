# 🐍 Snake Game

A classic Snake game implementation in Python with pygame. Smooth gameplay, score tracking, and a polished user interface.

## ✨ Features

- **Smooth Controls**: Play with keyboard arrows or WASD
- **Score System**: Track your current score and high score
- **Persistent High Scores**: High scores are saved to a file
- **Pause Mode**: Pause the game at any time
- **Game Over Screen**: Clear visual feedback with restart option
- **Responsive Design**: Works on different screen sizes

## 🎮 Controls

| Key | Action |
|-----|--------|
| ↑ / W | Move Up |
| ↓ / S | Move Down |
| ← / A | Move Left |
| → / D | Move Right |
| P | Pause Game |
| Q | Quit Game |

## 📦 Installation

### Prerequisites

- Python 3.7+
- Git

### Installation Steps

1. Clone this repository:
   ```bash
   git clone https://github.com/hal-urbana/snake.git
   cd snake
   ```

2. Install required packages:
   ```bash
   pip install pygame
   ```

3. Run the game:
   ```bash
   python snake/snake.py
   ```

## 🚀 Usage

Simply run the snake script:

```bash
python snake/snake.py
```

Or for development/testing:

```bash
python -m snake.snake
```

## 📄 License

This project is open source and available under the MIT License.

## 📚 Project Structure

```
snake/
├── snake.py          # Main game script
├── README.md         # This file
├── requirements.txt  # Python dependencies
├── highscore.txt     # Stores high score (created on first run)
└── LICENSE          # License information
```

## 🔧 Technical Details

### Game Mechanics

- **Grid System**: The game is played on a grid-based arena
- **Snake Body**: A list of segments tracked as the snake moves
- **Collision Detection**: Handles both wall collisions and self-collisions
- **Score Calculation**: 10 points per food item collected

### Code Structure

- **SnakeSegment**: Dataclass for individual snake body parts
- **Position**: Dataclass for game positions
- **SnakeGame**: Main game class handling all logic

## 🎯 Future Improvements

- [ ] Add power-ups
- [ ] Implement sound effects
- [ ] Add multiple difficulty levels
- [ ] Create AI opponent mode
- [ ] Add mobile touch controls
- [ ] Implement level progression

## 👤 Author

Created by hal-urbana

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📞 Contact

For questions or feedback, please open an issue on GitHub.

---

**Enjoy the game! 🎮🐍**