# MessageEntity

## Description

This object represents one special entity in a text message. For example, hashtags, usernames, URLs, etc.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the entity. Can be 'mention' (@username), 'hashtag' (#hashtag), 'cashtag' ($USD), 'bot_command' (/start@jobs_bot), 'url' (https://telegram.org), 'email' (do-not-reply@telegram.org), 'phone_number' (+1-212-555-0123), 'bold' (bold text), 'italic' (italic text), 'underline' (underlined text), 'strikethrough' (strikethrough text), 'code' (monowidth string), 'pre' (monowidth block), 'text_link' (for clickable text URLs), 'text_mention' (for users without usernames) |
| `offset` | `#!python int` | Offset in UTF-16 code units to the start of the entity |
| `length` | `#!python int` | Length of the entity in UTF-16 code units |
| `url` | `#!python Optional[str]` | Optional. For 'text_link' only, url that will be opened after user taps on the text |
| `user` | `#!python Optional[User]` | Optional. For 'text_mention' only, the mentioned user |
| `language` | `#!python Optional[str]` | Optional. For 'pre' only, the programming language of the entity text |



## Location

- `from aiogram.types import MessageEntity`
- `from aiogram.api.types import MessageEntity`
- `from aiogram.api.types.message_entity import MessageEntity`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#messageentity)
- [aiogram.types.User](../types/user.md)
