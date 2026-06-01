// Tiny pixel-sprite system. Each sprite is rows of characters mapped to colours
// through a shared palette ('.' or space = transparent). Rendered to a crisp
// pixelated canvas so the art stays sharp at any scale.

const PAL = {
  K: "#0c0820",  // outline / dark
  W: "#ffffff",  // highlight / eye white
  E: "#15131f",  // eye / pupil
  g: "#7fd957", G: "#4f9e2f", L: "#aef07a",      // slime greens
  p: "#b06cff", P: "#7d44c9",                      // wraith purples
  s: "#f1c899",                                    // skin
  b: "#4a6cf0", B: "#2e49b8",                      // robe blues
  t: "#d9a441", T: "#a8762a",                      // book / tan
  y: "#ffcf4d",                                    // gold glow
  h: "#9aa3c0", H: "#5d6488",                      // stone greys
  r: "#e85a6b",                                    // mouth / red
};

const SLIME = [
  "    KKKKKK",
  "  KKgggggggKK",
  " KgggggLgggggK",
  "KgggggggggggggK",
  "KgggEWgggEWgggK",
  "KgggEEgggEEgggK",
  "KgggggggggggggK",
  "KgggggrrrgggggK",
  " KgggggggggggK",
  "  KKKKKKKKKKK",
];

const WRAITH = [
  "    KKKKK",
  "   KppppppK",
  "  KpppppppppK",
  " KppPPPPPPPppK",
  " KppWEpppWEppK",
  " KpppEpppppEpK",
  " KppppppppppppK",
  " KpppppPPpppppK",
  " KppppppppppppK",
  "  KpKppKppKppK",
  "   K K  K  K",
];

const GOLEM = [
  "  KKKKKKKK",
  " KhhhhhhhhhK",
  "KhhHHhhhHHhhK",
  "KhhWEhhhWEhhK",
  "KhhhhhhhhhhhK",
  "KhhhrrrrrhhhK",
  "KHhhhhhhhhhHK",
  "KhttttttttthK",
  "KhtTtTtTtTthK",
  " KhhhhhhhhhK",
  "  KKK  KKK",
];

const SCHOLAR = [
  "    ppppp",
  "   pppppppp",
  "  pppPPPPppp",
  "  KssssssssK",
  "  KsWEssWEsK",
  "  Ksssssssss",
  "   bbbbbbbb",
  "  bbBBBBBBbb",
  " bbBBttttBBb",
  " bbBtTTTTtBb",
  " bbBttttttBb",
  "  bb    bb",
  "  KK    KK",
];

const MONSTERS = [
  { name: "Slime of Doubt", rows: SLIME },
  { name: "Knowledge Wraith", rows: WRAITH },
  { name: "Tome Golem", rows: GOLEM },
];

function spriteCanvas(rows, scale) {
  const h = rows.length;
  const w = Math.max(...rows.map((r) => r.length));
  const cv = document.createElement("canvas");
  cv.width = w * scale;
  cv.height = h * scale;
  cv.style.width = w * scale + "px";
  cv.style.height = h * scale + "px";
  cv.style.imageRendering = "pixelated";
  const ctx = cv.getContext("2d");
  rows.forEach((row, y) => {
    [...row].forEach((ch, x) => {
      const c = PAL[ch];
      if (c) {
        ctx.fillStyle = c;
        ctx.fillRect(x * scale, y * scale, scale, scale);
      }
    });
  });
  return cv;
}

window.Sprites = {
  monsters: MONSTERS,
  scholar: SCHOLAR,
  randomMonster() {
    return MONSTERS[Math.floor(Math.random() * MONSTERS.length)];
  },
  draw(rows, scale = 11) {
    return spriteCanvas(rows, scale);
  },
};
