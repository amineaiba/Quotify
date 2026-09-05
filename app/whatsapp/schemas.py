from pydantic import BaseModel, Field

# Meta's webhook payload shape — kept separate from app/schemas/ because this
# belongs to Meta's API, not ours. Only the fields we read are modeled;
# `messages`/`statuses` are optional because the same URL also receives
# delivery-receipt payloads that carry no `messages` at all.


class TextBody(BaseModel):
    body: str


class ContactProfile(BaseModel):
    name: str | None = None


class Contact(BaseModel):
    profile: ContactProfile = ContactProfile()
    wa_id: str


class WhatsAppMessage(BaseModel):
    id: str
    from_: str = Field(alias="from")
    type: str
    text: TextBody | None = None


class Metadata(BaseModel):
    phone_number_id: str


class ChangeValue(BaseModel):
    metadata: Metadata
    contacts: list[Contact] = []
    messages: list[WhatsAppMessage] = []


class Change(BaseModel):
    value: ChangeValue


class Entry(BaseModel):
    changes: list[Change] = []


class WebhookPayload(BaseModel):
    entry: list[Entry] = []


class InboundMessage(BaseModel):
    """One text message, flattened out of the nested payload."""

    phone_number_id: str
    from_number: str
    contact_name: str | None
    whatsapp_message_id: str
    text: str


def extract_text_messages(payload: WebhookPayload) -> list[InboundMessage]:
    """Pulls out only text messages — statuses and non-text messages are skipped."""
    result: list[InboundMessage] = []
    for entry in payload.entry:
        for change in entry.changes:
            value = change.value
            names_by_wa_id = {c.wa_id: c.profile.name for c in value.contacts}
            for message in value.messages:
                if message.type != "text" or message.text is None:
                    continue
                result.append(
                    InboundMessage(
                        phone_number_id=value.metadata.phone_number_id,
                        from_number=message.from_,
                        contact_name=names_by_wa_id.get(message.from_),
                        whatsapp_message_id=message.id,
                        text=message.text.body,
                    )
                )
    return result
