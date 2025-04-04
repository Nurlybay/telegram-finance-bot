from sqlalchemy import Table, MetaData, Column, BigInteger, String, DateTime,ForeignKey,Integer

metadata = MetaData()


users = Table(
    "users",
    metadata,
    Column("telegram_id", Integer, primary_key=True),  # Use telegram_id as primary key
    Column("first_name", String, nullable=False),
    Column("last_name", String)
)

# New messages table
messages_table = Table(
    "messages",
    metadata,
    Column("id", Integer, primary_key=True),  # Still need a primary key for messages
    Column("telegram_id", Integer, ForeignKey("users.telegram_id"), nullable=False),  # Direct reference to user's telegram_id
    Column("content", String),  # The transcribed text
    Column("timestamp", DateTime)  # When the message was sent
)

# users = Table(
#     "users",
#     metadata,
#     Column("telegram_id", BigInteger, primary_key=True),
#     Column("first_name", String),
#     Column("last_name", String),
#     extend_existing=True 
# )

# messages_table = Table(
#     "messages",
#     metadata,
#     Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
#     Column("content", String),  # The transcribed text
#     Column("timestamp", DateTime),  # When the message was sent
#     Column("message_type", String)  # Optional: to track if it was voice, text, etc.
# )