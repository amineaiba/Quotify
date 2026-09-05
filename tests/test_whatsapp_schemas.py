from app.whatsapp.schemas import WebhookPayload, extract_text_messages

TEXT_MESSAGE_PAYLOAD = {
    "entry": [
        {
            "changes": [
                {
                    "value": {
                        "metadata": {"phone_number_id": "123456"},
                        "contacts": [{"profile": {"name": "Yacine"}, "wa_id": "213555000000"}],
                        "messages": [
                            {
                                "id": "wamid.1",
                                "from": "213555000000",
                                "type": "text",
                                "text": {"body": "chhal 500 flyers?"},
                            }
                        ],
                    }
                }
            ]
        }
    ]
}

STATUS_ONLY_PAYLOAD = {
    "entry": [
        {
            "changes": [
                {
                    "value": {
                        "metadata": {"phone_number_id": "123456"},
                        "statuses": [{"id": "wamid.1", "status": "delivered"}],
                    }
                }
            ]
        }
    ]
}

IMAGE_MESSAGE_PAYLOAD = {
    "entry": [
        {
            "changes": [
                {
                    "value": {
                        "metadata": {"phone_number_id": "123456"},
                        "messages": [{"id": "wamid.2", "from": "213555000000", "type": "image"}],
                    }
                }
            ]
        }
    ]
}


def test_extract_text_messages_from_real_payload():
    payload = WebhookPayload.model_validate(TEXT_MESSAGE_PAYLOAD)
    messages = extract_text_messages(payload)

    assert len(messages) == 1
    assert messages[0].phone_number_id == "123456"
    assert messages[0].from_number == "213555000000"
    assert messages[0].contact_name == "Yacine"
    assert messages[0].whatsapp_message_id == "wamid.1"
    assert messages[0].text == "chhal 500 flyers?"


def test_extract_text_messages_ignores_status_only_payload():
    payload = WebhookPayload.model_validate(STATUS_ONLY_PAYLOAD)
    assert extract_text_messages(payload) == []


def test_extract_text_messages_ignores_non_text_messages():
    payload = WebhookPayload.model_validate(IMAGE_MESSAGE_PAYLOAD)
    assert extract_text_messages(payload) == []
