# Bjorn Discord Bot

Bjorn is a Discord bot built using the discord.py framework, designed to enhance server management and gaming experiences with a focus on League of Legends customs.

## Features

### League of Legends Customs
- **Custom Games Management**: Create and manage custom games with fair team balancing
- **MMR System**: Track player ratings with a sophisticated MMR system
- **Statistics**: View detailed player and match statistics
- **Team Generation**: Automatically create balanced teams based on player skill levels
- **Queue System**: Manage custom game queues with a user-friendly interface
- **Draft Links**: Automatically generate draftlol.dawe.gg links for champion drafting

### Voice Channel Management
- **BetterVC**: Dynamically manage voice channels, automatically hiding empty channels
- **Arena Teams**: Generate random teams from players in a voice channel

### Role Management
- **Role On Join**: Automatically assign roles to new members
- **Reaction Roles**: Allow users to self-assign roles by reacting to messages

### Moderation
- **Strike System**: Issue warnings to users with configurable thresholds

### Utility
- **Server Information**: Display detailed information about the server
- **User Information**: Show user profiles and details
- **Bot Status**: Check bot uptime, ping, and system information

## Requirements

- Python 3.10+
- Discord.py 2.2.2+
- Docker (for containerized deployment)
- SQLite3 (for database storage)
- Additional dependencies listed in requirements.txt

## Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bjorn.git
   cd bjorn
   ```

2. Create configuration files:
   - Copy `.env.example` to `.env` and modify as needed
   - Create `.env.secret` with your Discord bot token

3. Build and run with Docker Compose:
   ```bash
   sudo docker compose up -d --build
   ```

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bjorn.git
   cd bjorn
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create configuration files:
   - Copy `.env.example` to `.env` and modify as needed
   - Create `.env.secret` with your Discord bot token

4. Run the bot:
   ```bash
   python src/main.py
   ```

## Configuration

### Environment Variables

Create a `.env.secret` file with the following variables:
- `TOKEN`: Your Discord bot token
- `DEV`: Set to "True" for development mode
- `TEST_EXTENSION`: Extension to test in development mode

Create a `.env` file with these variables:
- `PREFIX`: Command prefix (default: `¤`)
- `DEV_TEST_CATEGORY_NAME`: Category name for test channels
- `DEV_TEST_CHANNEL_NAME`: Prefix for test channel names
- `LEAGUE_GRAPH_DIR`: Directory for storing league graphs
- `LEAGUE_GRAPH_FILENAME`: Filename for league graph images
- `DATA_DIR`: Directory for storing data
- `LEAGUE_DB_NAME`: Name for the league database
- `CONFIG_DB_NAME`: Name for the configuration database

## Usage

### League Commands

- `/league queue` - Create a customs queue for fair team balancing
- `/league free_teams` - Create custom teams manually
- `/league arena` - Generate teams from voice channel members
- `/league rating set` - Set a player's MMR
- `/league rating get` - Get a player's rank or MMR
- `/league rating graph` - View a player's MMR history graph
- `/league statistics general` - View general player statistics
- `/league statistics teamates_enemies` - View statistics about teammates and opponents
- `/league matches` - Display a player's match history

### Role Management

- `/roleonjoin show_roles` - Show roles assigned automatically on join
- `/roleonjoin set_role` - Set a role to be assigned on join
- `/roleonjoin remove_role` - Remove a role from auto-assignment
- `/add_reaction_role` - Add a reaction role to a message

### Voice Channel Management

- `/bettervc_manage show_category` - Show BetterVC categories
- `/bettervc_manage set_category` - Set a category for BetterVC management
- `/bettervc_manage remove_category` - Remove a category from BetterVC management

### Strike System

- `/strike how_many_warnings` - Check how many warnings a user has
- `/strike add_warning` - Add a warning to a user

### Utility Commands

- `/info ping` - Check bot latency
- `/info uptime` - Check bot uptime
- `/info bot` - Show bot information
- `/info server` - Show server information
- `/info user` - Show user information

### Administrative Commands

- `/sync` - Sync slash commands
- `/devchannel` - Create a development channel
- `/adminmanage show_roles` - Show admin roles
- `/adminmanage set_role` - Set an admin role
- `/adminmanage remove_role` - Remove an admin role

## Development

To run the bot in development mode:

```bash
docker compose --profile dev run --service-ports bot_dev
```

To access a shell in the development container:

```bash
docker compose --profile dev run --service-ports bot_dev sh
```

### Database Management

To copy the league database over SSH:

```bash
scp p@192.168.3.5:/home/p/bjorn/data/league.sqlite league.sqlite
```

### Code Style

This project uses the Black formatter for code styling.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
