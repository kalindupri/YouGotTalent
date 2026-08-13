import uuid

from sqlalchemy.orm import Session

from app.core import discord_bot
from app.core.config import settings
from app.models.support_chat import SupportConversation, SupportConversationStatus, SupportMessage, SupportMessageSender
from app.models.user import User


def start_conversation(db: Session, question: str, user: User | None) -> SupportConversation:
    label = user.full_name if user else f"Guest-{uuid.uuid4().hex[:6]}"
    thread_id, message_id = discord_bot.create_thread(
        channel_id=settings.DISCORD_SUPPORT_CHANNEL_ID,  # type: ignore[arg-type]
        name=f"chat-{label}"[:100],
        initial_message=f"**{label}** couldn't get an answer from the help bot:\n\n{question}",
    )
    conversation = SupportConversation(
        user_id=user.id if user else None,
        guest_label=None if user else label,
        discord_thread_id=thread_id,
        last_seen_discord_message_id=message_id,
        status=SupportConversationStatus.OPEN.value,
    )
    conversation.messages.append(SupportMessage(sender=SupportMessageSender.CUSTOMER.value, content=question))
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def add_customer_message(db: Session, conversation: SupportConversation, content: str) -> SupportMessage:
    message = SupportMessage(conversation_id=conversation.id, sender=SupportMessageSender.CUSTOMER.value, content=content)
    db.add(message)
    discord_bot.post_to_channel(conversation.discord_thread_id, content)
    db.commit()
    db.refresh(message)
    return message


def sync_agent_replies(db: Session, conversation: SupportConversation) -> None:
    """Best-effort: a Discord hiccup here shouldn't break polling for the customer, it just means
    this particular poll doesn't pick up anything new (the next one will).
    """
    try:
        new_messages = discord_bot.get_new_human_messages(conversation.discord_thread_id, conversation.last_seen_discord_message_id)
    except Exception:
        return
    if not new_messages:
        return
    for m in new_messages:
        db.add(SupportMessage(conversation_id=conversation.id, sender=SupportMessageSender.AGENT.value, content=m["content"]))
    conversation.last_seen_discord_message_id = new_messages[-1]["id"]
    db.commit()


def get_conversation(db: Session, conversation_id: uuid.UUID) -> SupportConversation | None:
    return db.query(SupportConversation).filter(SupportConversation.id == conversation_id).first()
