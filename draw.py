#!/usr/bin/env python3
"""Render entry.png: Monday 23 November 2026 as a newspaper front page.

One 1024x1024 page drawn with PIL: a masthead with the date, a wide
lead card on the NVIDIA reversal, three rows of paired story cards,
one wide summit card, and a small-print ticker along the foot. All
copy is wrapped from real text measurements and each card shrinks
its type until the block fits, so no line can spill or clip.
"""

import os

from PIL import Image, ImageDraw, ImageFont

SIDE = 1024
EDGE = 34
WIDTH = SIDE - 2 * EDGE
GAP = 12

PAPER = (248, 244, 233)
BLACK = (30, 27, 23)
CRIMSON = (158, 28, 28)
KICKER = (140, 32, 26)
BORDER = (150, 134, 100)
FOOT = (96, 88, 72)

FONTS = "/usr/share/fonts/truetype/liberation"
SERIF = os.path.join(FONTS, "LiberationSerif-Bold.ttf")
BOLD = os.path.join(FONTS, "LiberationSans-Bold.ttf")
PLAIN = os.path.join(FONTS, "LiberationSans-Regular.ttf")


def typeface(path, size):
    return ImageFont.truetype(path, size)


def measure_wrap(draw, text, fnt, max_w):
    """Split text into lines that each measure within max_w."""
    out = []
    line = ""
    for word in text.split():
        trial = word if line == "" else line + " " + word
        if draw.textlength(trial, font=fnt) <= max_w:
            line = trial
        else:
            if line:
                out.append(line)
            line = word
    if line:
        out.append(line)
    return out


def largest_fitting(draw, text, path, start, max_w, max_lines, floor=10):
    """Biggest face from start down that wraps within max_lines."""
    size = start
    while size > floor:
        fnt = typeface(path, size)
        widest = max(draw.textlength(w, font=fnt) for w in text.split())
        if widest <= max_w and len(measure_wrap(draw, text, fnt, max_w)) <= max_lines:
            return fnt
        size -= 1
    return typeface(path, floor)


def centre_line(draw, y, text, fnt, fill):
    w = draw.textlength(text, font=fnt)
    draw.text(((SIDE - w) / 2, y), text, font=fnt, fill=fill)
    return y + round(fnt.size * 1.18)


def story_panel(draw, rect, kicker, headline, body,
                head_start=30, body_start=21, head_cap=3, body_cap=7,
                accent=False):
    """One bordered story: kicker, headline and body, auto-shrunk.
    The lead story passes accent=True and gets a heavy crimson frame
    so the page hierarchy reads at a glance."""
    x0, y0, x1, y1 = rect
    if accent:
        draw.rectangle(rect, outline=CRIMSON, width=3)
    else:
        draw.rectangle(rect, outline=BORDER, width=1)
    inset = 13
    inner_w = (x1 - x0) - 2 * inset
    inner_h = (y1 - y0) - 2 * inset

    kicker_fnt = typeface(BOLD, 13)
    factor = 1.0
    head_fnt = typeface(SERIF, head_start)
    body_fnt = typeface(PLAIN, body_start)
    head_lines = measure_wrap(draw, headline, head_fnt, inner_w)
    body_lines = measure_wrap(draw, body, body_fnt, inner_w)
    block_h = 0
    while factor > 0.5:
        head_fnt = typeface(SERIF, max(11, round(head_start * factor)))
        body_fnt = typeface(PLAIN, max(9, round(body_start * factor)))
        head_lines = measure_wrap(draw, headline, head_fnt, inner_w)
        body_lines = measure_wrap(draw, body, body_fnt, inner_w)
        block_h = (17 + 6
                   + len(head_lines) * round(head_fnt.size * 1.14)
                   + 5
                   + len(body_lines) * round(body_fnt.size * 1.26))
        if (block_h <= inner_h and len(head_lines) <= head_cap
                and len(body_lines) <= body_cap):
            break
        factor -= 0.05

    y = y0 + inset + max(0, (inner_h - block_h) // 2)
    draw.text((x0 + inset, y), kicker.upper(), font=kicker_fnt, fill=KICKER)
    y += 17 + 6
    for line in head_lines:
        draw.text((x0 + inset, y), line, font=head_fnt, fill=BLACK)
        y += round(head_fnt.size * 1.14)
    y += 5
    for line in body_lines:
        draw.text((x0 + inset, y), line, font=body_fnt, fill=BLACK)
        y += round(body_fnt.size * 1.26)


def build_page():
    page = Image.new("RGB", (SIDE, SIDE), PAPER)
    draw = ImageDraw.Draw(page)

    # Masthead and date line
    masthead = "THE WORLD IN ONE PAGE"
    mast_fnt = largest_fitting(draw, masthead, SERIF, 66, WIDTH, 1)
    centre_line(draw, 30, masthead, mast_fnt, BLACK)

    dateline = "MONDAY 23 NOVEMBER 2026"
    date_fnt = largest_fitting(draw, dateline, BOLD, 46, WIDTH, 1)
    centre_line(draw, 110, dateline, date_fnt, CRIMSON)

    draw.line([(EDGE, 172), (SIDE - EDGE, 172)], fill=CRIMSON, width=4)
    draw.line([(EDGE, 180), (SIDE - EDGE, 180)], fill=BLACK, width=1)

    col_w = (WIDTH - GAP) // 2
    lx = EDGE
    rx = EDGE + col_w + GAP

    # Lead: the NVIDIA reversal and the market rebound
    story_panel(
        draw, (EDGE, 194, SIDE - EDGE, 334),
        "Markets · Silicon Valley",
        "NVIDIA Reinstates Huang as CEO; Shares Jump 33%",
        "NVIDIA brought back Jensen Huang as chief executive just 11 "
        "days after he resigned. Shares leapt about 33% and the S&P 500 "
        "surged 4.82% in a sharp rebound from last week's AI sell-off, "
        "even as Japan's Nikkei fell more than 5%.",
        head_start=42, body_start=24, head_cap=2, body_cap=4,
        accent=True,
    )

    # Row one: Benghazi and the Iran sanctions
    story_panel(
        draw, (lx, 344, lx + col_w, 494),
        "War · Benghazi",
        "Ukraine Says It Sank Russian Corvette off Libya",
        "Ukraine said seven naval drones sank the Russian corvette "
        "Merkury at Benghazi port. A UN mission urged an independent "
        "probe into the attacks on the port.",
    )
    story_panel(
        draw, (rx, 344, rx + col_w, 494),
        "Sanctions · Washington",
        "US Unveils Sweeping Sanctions on Iran Networks",
        "The US Treasury sanctioned Iran's shadow-banking network, "
        "which Secretary Bessent called the regime's last financial "
        "lifeline; some $14.7B in linked deals were identified.",
    )

    # Row two: the House result and the Dymer strike toll
    story_panel(
        draw, (lx, 504, lx + col_w, 654),
        "Politics · Washington",
        "Democrats Win Biggest House Majority Since 1992",
        "Democrats secured at least 258 House seats, their largest "
        "majority since 1992, after flipping a seat in North Carolina "
        "as the final counts came in.",
    )
    story_panel(
        draw, (rx, 504, rx + col_w, 654),
        "War · Ukraine",
        "Dymer Apartment Strike Toll Rises to at Least 11",
        "The death toll from a Russian strike on an apartment block "
        "in Dymer, near Kyiv, rose to at least 11, rescuers said, "
        "after another night of attacks.",
    )

    # Row three: the AI summit and the Congo Ebola fight
    story_panel(
        draw, (lx, 664, lx + col_w, 814),
        "Technology · Barbados",
        "UN Chief Urges Tighter AI Rules at Bridgetown",
        "UN Secretary-General Guterres urged greater regulation of "
        "artificial intelligence at the Bridgetown Special Summit on "
        "AI Safety in Barbados.",
    )
    story_panel(
        draw, (rx, 664, rx + col_w, 814),
        "Health · DR Congo",
        "Fighting in Ituri Disrupts Ebola Response",
        "Heavy fighting in Ituri disrupted the Ebola response, with "
        "WHO teams sheltering in a maternity ward; infections top "
        "11,700, with 5,775 deaths.",
    )

    # Wide card: the three-way summit in Shenzhen
    story_panel(
        draw, (EDGE, 824, SIDE - EDGE, 934),
        "Diplomacy · Shenzhen",
        "Trump, Xi and Putin Hold First Three-Way Summit",
        "The leaders of the United States, China and Russia met in "
        "Shenzhen for their first three-way summit and pledged talks "
        "on reducing nuclear risk.",
        head_start=32, body_start=20, head_cap=2, body_cap=3,
    )

    # Small-print ticker along the foot of the page
    ticker = (
        "India pledges about \u20ac1.4B to rebuild Nepal after a deadly "
        "glacier flood \u2022 EU proposes a 22nd sanctions package "
        "against Russia \u2022 South Korea's president names the "
        "country's first woman spy chief in a surprise reshuffle "
        "\u2022 At least 24 mourners die as a boat capsizes in "
        "Nigeria's Bayelsa State \u2022 FBI probes an apparent hack "
        "of its NCIC crime database"
    )
    tick_fnt = largest_fitting(draw, ticker, PLAIN, 15, WIDTH, 3)
    draw.line([(EDGE, 940), (SIDE - EDGE, 940)], fill=BORDER, width=1)
    y = 948
    for line in measure_wrap(draw, ticker, tick_fnt, WIDTH)[:3]:
        centre_line(draw, y, line, tick_fnt, FOOT)
        y += round(tick_fnt.size * 1.32)

    here = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(here, "entry.png")
    page.save(target, format="PNG", optimize=True)
    print("wrote", target)


if __name__ == "__main__":
    build_page()
