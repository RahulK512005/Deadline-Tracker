"""Unit tests for NotificationService and Twilio integration."""
import pytest
from unittest.mock import patch, MagicMock
from services.notification_service import NotificationService, format_phone_number


def test_format_phone_number():
    # 10 digit Indian numbers without country code
    assert format_phone_number("8310905835") == "+918310905835"
    assert format_phone_number("831 090 5835") == "+918310905835"
    assert format_phone_number("831-090-5835") == "+918310905835"

    # Already formatted numbers
    assert format_phone_number("+918310905835") == "+918310905835"
    assert format_phone_number("+14155238886") == "+14155238886"

    # 12 digit with 91 prefix
    assert format_phone_number("918310905835") == "+918310905835"

    # Empty
    assert format_phone_number("") == ""


def test_send_whatsapp_missing_credentials():
    service = NotificationService()
    success, msg = service.send_whatsapp("Test message", to_number="+918310905835")
    assert not success
    assert "missing" in msg.lower() or "required" in msg.lower()


def test_send_whatsapp_success():
    service = NotificationService({
        "twilio_account_sid": "ACmockedsid12345678901234567890",
        "twilio_auth_token": "mockedtoken1234567890",
        "twilio_from_number": "+14155238886",
        "twilio_to_number": "+918310905835"
    })

    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"sid": "SMmockedmessagesid123"}

    with patch("requests.post", return_value=mock_resp) as mock_post:
        success, msg = service.send_whatsapp("Deadline reminder: Math assignment due tomorrow!")
        assert success
        assert "SMmockedmessagesid123" in msg

        # Validate mock call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "ACmockedsid12345678901234567890" in args[0]
        assert kwargs["auth"] == ("ACmockedsid12345678901234567890", "mockedtoken1234567890")
        assert kwargs["data"]["From"] == "whatsapp:+14155238886"
        assert kwargs["data"]["To"] == "whatsapp:+918310905835"
        assert kwargs["data"]["Body"] == "Deadline reminder: Math assignment due tomorrow!"


def test_send_sms_success():
    service = NotificationService({
        "twilio_account_sid": "ACmockedsid12345678901234567890",
        "twilio_auth_token": "mockedtoken1234567890",
        "twilio_from_number": "+1234567890",
        "twilio_to_number": "+918310905835"
    })

    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"sid": "SMsmstest123"}

    with patch("requests.post", return_value=mock_resp) as mock_post:
        success, msg = service.send_sms("Short SMS reminder")
        assert success
        assert "SMsmstest123" in msg

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["data"]["From"] == "+1234567890"
        assert kwargs["data"]["To"] == "+918310905835"
        assert kwargs["data"]["Body"] == "Short SMS reminder"


def test_twilio_api_failure():
    service = NotificationService({
        "twilio_account_sid": "ACmockedsid",
        "twilio_auth_token": "mockedtoken",
        "twilio_from_number": "+14155238886",
        "twilio_to_number": "+918310905835"
    })

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"message": "Invalid To Phone Number"}

    with patch("requests.post", return_value=mock_resp):
        success, msg = service.send_whatsapp("Test fail")
        assert not success
        assert "Invalid To Phone Number" in msg
