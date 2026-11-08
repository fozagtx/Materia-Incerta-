import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

const LATIN = "U+0000-024F, U+2000-206F, U+20AC, U+2122, U+2190-21FF, U+2212, U+2215, U+2460-24FF, U+00B7";
const GREEK = "U+0370-03FF, U+1F00-1FFF";

const faces: Parameters<typeof loadFont>[0][] = [];
for (const weight of ["400", "500", "600"]) {
  for (const style of ["normal", "italic"]) {
    faces.push({ family: "EB Garamond", url: staticFile(`fonts/eb-garamond-latin-${weight}-${style}.woff2`), weight, style, unicodeRange: LATIN });
    faces.push({ family: "EB Garamond", url: staticFile(`fonts/eb-garamond-greek-${weight}-${style}.woff2`), weight, style, unicodeRange: GREEK });
  }
}
for (const weight of ["400", "500", "600", "700"]) {
  faces.push({ family: "Inter", url: staticFile(`fonts/inter-latin-${weight}-normal.woff2`), weight });
}
for (const weight of ["400", "500"]) {
  faces.push({ family: "JetBrains Mono", url: staticFile(`fonts/jetbrains-mono-latin-${weight}-normal.woff2`), weight });
}

export const fontsReady = Promise.all(faces.map((f) => loadFont(f)));
