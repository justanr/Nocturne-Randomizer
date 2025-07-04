import nocturne_script_assembler as nass
import math

# Lots of this code was copied from the regular assembler. Would be better to not do it quite this way just for consolidation purposes, but I'd rather not have to account for this specific case in the main assembler. This specific case needs to not change the STRINGS section (as it doesn't exist here).


def bbtoi(byte_array):
    retint = 0
    current_power = 0
    for byte in byte_array:
        retint += byte * math.pow(256, current_power)
        current_power += 1
    return int(retint)


def changeItemMessageByIndex(message_script, message_obj, index):
    indexed_message = message_script.messages[index]
    absolute_pointer = message_script.message_pointers[index].pointer

    # Calculate header size
    if message_obj.is_decision:
        header_size = 0x18 + 12 + (len(message_obj.relative_pointers) * 4)
    else:
        header_size = 0x18 + 8 + (len(message_obj.relative_pointers) * 4)

    # Turn the relative pointers into fully functional pointers
    message_obj.text_pointers = []
    for rp in message_obj.relative_pointers:
        message_obj.text_pointers.append(rp + absolute_pointer + header_size)

    # Swap the object in
    message_script.messages[index] = message_obj

    # Change the offset of each of the next message pointers
    byte_len = len(message_obj.toBytes())
    delta_bytes = byte_len - len(indexed_message.toBytes())
    for mp in message_script.message_pointers:
        if mp.pointer > absolute_pointer:  # + byte_len?
            mp.pointer += delta_bytes

    # Update all text pointers past this since they're absolute
    for c, mobj in enumerate(message_script.messages):
        for i, tp in enumerate(
            mobj.text_pointers
        ):  # This is probably computationally bad but meh
            if index != c and tp > absolute_pointer:
                mobj.text_pointers[i] += delta_bytes

    # strings_obj.count+=delta_bytes #Don't need to move the strings object since it doesn't exist
    message_script.m_size += delta_bytes

    # Update other affected pointers
    message_script.names.names_pointers = [
        x + delta_bytes for x in message_script.names.names_pointers
    ]
    message_script.names.offset += delta_bytes
    message_script.rolling_pointer += delta_bytes
    return 0


byte_array = nass.filenameToBytes("patches/unmodded_items.msg")

# Section 03 - Messages
#   In essence its own file type.
# 1 byte (technically 4): Always 07. Indicates MSG file type?
# 4 bytes of file size. Should match value at 0x58
# 4 bytes of "magic". "MSG1"
# 4 bytes of 00
# 4 bytes of ??
# 4 bytes of ??
# 4 bytes - entry count of pointers
# Maybe something after? 00 00 02 00.

c_off = 0
msg_script = nass.message_script()
msg_script.type = bbtoi(byte_array[c_off : c_off + 4])
if msg_script.type != 7:
    print(
        "Warning? Message file type not 7. Type:",
        hex(s.sections[MESSAGES].type),
        "Reading from",
        hex(c_off),
    )
msg_script.m_size = bbtoi(byte_array[c_off + 4 : c_off + 8])
msg_script.magic = [chr(x) for x in byte_array[c_off + 8 : c_off + 12]]
# 12:16 is 0's
msg_script.rolling_pointer = bbtoi(
    byte_array[c_off + 16 : c_off + 20]
)  # pointer to gibberish section
msg_script.rolling_size = bbtoi(
    byte_array[c_off + 20 : c_off + 24]
)  # size of gibberish section
msg_script.pointers_count = bbtoi(byte_array[c_off + 24 : c_off + 28])
msg_script.unknown_value = bbtoi(byte_array[c_off + 28 : c_off + 32])  # 0x20000 (?)

# Pointer entry start.
#   Size: 0x08
# 4 bytes of 00 00 00 00 or 01 00 00 00. Boolean value?
# 4 bytes of offset (relative to section start)

c_off += 32
m_off = c_off  # save the message offset used for later
for i in range(msg_script.pointers_count):
    bval = bbtoi(byte_array[c_off : c_off + 4])
    mpointer = bbtoi(byte_array[c_off + 4 : c_off + 8])
    msg_script.message_pointers.append(nass.message_pointer(bval, mpointer))
    c_off += 8

# Names in script - header
#   Size: 0x10
# 4 bytes of offset
# 4 bytes of name count
# 8 bytes of 00

n_off = bbtoi(byte_array[c_off : c_off + 4])
n_count = bbtoi(byte_array[c_off + 4 : c_off + 8])
msg_script.names = nass.names_obj(n_off, n_count)
# 8 0's #c_off+=16

# Names in script - NC = Name Count
# Pointers(?) - 4 bytes * NC
# Names delimited by 00

c_off = m_off + n_off
n_pointers = []
for i in range(n_count):
    n_pointers.append(bbtoi(byte_array[c_off : c_off + 4]))
    c_off += 4
n_strings = []
for p in n_pointers:
    c_off = m_off + p
    c = byte_array[c_off]
    n_str = ""
    while c != 0:
        n_str += chr(c)
        c_off += 1
        c = byte_array[c_off]
    n_strings.append(n_str)
msg_script.names.names_pointers = n_pointers
msg_script.names.names = n_strings

# Messages
#   Size: Variable
# 0x18 bytes of label string
# 2 bytes of textbox count
#   if textbox count > 0 - Is not a decision text
# 2 bytes of speaker name ID. Note: -1 (FFFF) is viable.
# 4 bytes of text pointer * textbox count
# 4 bytes of text length in bytes (starting right after this)
# text length bytes of text string
#   if textbox count == 0 - Is a decision text
# 2 bytes of actual textbox count
# 4 bytes of 0 (I think?)
# 4 bytes of text pointer * textbox count
# 4 bytes of text length in bytes (starting right after this)
# use the pointers get to the message objects
for mp_obj in msg_script.message_pointers:
    p = mp_obj.pointer
    c_off = m_off + p
    m = nass.message()
    l_str = ""
    for j in range(0x18):
        c = byte_array[c_off + j]
        if c == 0:
            break
        l_str += chr(c)
    m.label_str = l_str
    c_off += 0x18
    m.textbox_count = bbtoi(byte_array[c_off : c_off + 2])
    if m.textbox_count == 0:  # structured differently for decision text
        m.textbox_count = bbtoi(byte_array[c_off + 2 : c_off + 4])
        m.is_decision = True
        m.name_id = 0xFFFF  # isn't going to be stored but just setting it
        c_off += 4  # 4 bytes of 0
    else:
        m.name_id = bbtoi(byte_array[c_off + 2 : c_off + 4])
    c_off += 4
    for i in range(m.textbox_count):
        m.text_pointers.append(bbtoi(byte_array[c_off : c_off + 4]))
        c_off += 4
    m.text_size = bbtoi(byte_array[c_off : c_off + 4])
    c_off += 4
    m.text_bytes = byte_array[c_off : c_off + m.text_size]
    m.byte_formed = True
    msg_script.messages.append(m)

# A list of rolling offsets to the pointers in the message script.
# The values are the offset from the previous pointer by every other byte. It starts with 2 and a bunch of 4's because the first pointer is after the 4 byte boolean value, then each pointer object has a length of 8.
# This is used to turn the pointers from pointers relative to the message script to pointers absolute in memory.
# One last thing: W H Y ? ? ?
r_p = msg_script.rolling_pointer
r_s = msg_script.rolling_size
msg_script.rolling_offsets = byte_array[
    m_off + r_p - 0x20 : m_off + r_p + r_s - 0x20
]  # for some reason the pointer offset is before the message header instead of after like the other instances?

useless_item_descs = [
    0x21,
    0x2F,
    0x30,
    0x31,
    0x32,
    0x33,
    0x39,
    0x3B,
    0x3C,
    0x3E,
    0x3F,
    0x4B,
    0x4C,
    0x4D,
    0x4E,
    0x51,
    0x52,
    0x54,
    0x56,
    0x58,
    0x59,
    0x5A,
    0x5B,
    0x5C,
    0x5D,
    0x5E,
    0x5F,
]

useless_item_msgs = []
for i in useless_item_descs:
    short_msg = nass.message("a", "item_" + hex(i))
    changeItemMessageByIndex(msg_script, short_msg, i)
black_key_msg = nass.message(
    "^.^iThe key for the^nBlack Amala Temple.^n^0", "item_91", False
)
white_key_msg = nass.message(
    "^.^iThe key for the^nWhite Amala Temple.^n^0", "item_92", False
)
red_key_msg = nass.message(
    "^.^iThe key for the^nRed Amala Temple.^n^n^0", "item_93", False
)
apocalypse_msg = nass.message(
    "^.^iA stone that attracts^nthe 4 horsemen.^n^0", "item_94", False
)
goblet_msg = nass.message(
    "^.^iA mother skeleton's^nfavorite cup.^n^0", "item_95", False
)
eggplant_msg = nass.message(
    "^.^iThe missing piece for^na suspicious ritual.^nIt is very plump^nwith excellent girth.^n^0",
    "item_96",
    False,
)
ikebukuro_msg = nass.message(
    "^.^iThe key to entering^nIkebukuro tunnel^n^0", "item_97", False
)
changeItemMessageByIndex(msg_script, black_key_msg, 0x91)
changeItemMessageByIndex(msg_script, white_key_msg, 0x92)
changeItemMessageByIndex(msg_script, red_key_msg, 0x93)
changeItemMessageByIndex(msg_script, apocalypse_msg, 0x94)
changeItemMessageByIndex(msg_script, goblet_msg, 0x95)
changeItemMessageByIndex(msg_script, eggplant_msg, 0x96)
changeItemMessageByIndex(msg_script, ikebukuro_msg, 0x97)
# unused_key_items = [0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9a, 0x9b, 0x9c, 0x9d, 0x9e, 0x9f]
piped_bytes = msg_script.toBytes()
if len(piped_bytes) > 0x3970:
    print(
        "Exporting item messages failed. New message script size is",
        str(0x3970 - len(piped_bytes)),
        "too large",
    )
else:
    nass.bytesToFile(piped_bytes, "patches/items.msg")
    print("Successfully updated item messages")
