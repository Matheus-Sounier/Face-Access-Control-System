import cvzone

def draw_face_box(img, x, y, w, h):
    return cvzone.cornerRect(img, (x, y, w, h), rt=0)

def draw_result(img, x, y, data):
    if data and data.get("match"):
        name = data.get("name", "Unknown")
        access_granted = data.get("access_granted", False)

        text_color = (
            (0, 255, 0)
            if access_granted
            else (0, 0, 255)
        )

        cvzone.putTextRect(
            img,
            name,
            (x, y - 10),
            colorT=text_color,
            scale=1.5,
        )

    else:
        cvzone.putTextRect(
            img,
            "Unknown",
            (x, y - 10),
            colorR=(0, 0, 255),
        )