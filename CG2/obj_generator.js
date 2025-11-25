/* 
Fausto Izquierdo - 24 de noviembre 2025
Desarrollo de Generador de Edificios 3D 
*/

const fs = require("fs");
const { V3 } = require("./V3.js");

function fmt(n) {
  return n.toFixed(4);
}

function main() {
  const args = process.argv.slice(2);

  // parámetros con valores por defecto
  const sides = args[0] ? parseInt(args[0]) : 8;
  const h = args[1] ? parseFloat(args[1]) : 6.0;
  const r1 = args[2] ? parseFloat(args[2]) : 1.0;
  const r2 = args[3] ? parseFloat(args[3]) : 0.8;

  // validación
  if (sides < 3 || sides > 36 || isNaN(sides) || h <= 0 || r1 <= 0 || r2 <= 0) {
    console.error(
      "Error: sides debe estar entre 3-36 y h, r1, r2 deben ser > 0"
    );
    return;
  }

  // arreglos: vertices, normales y caras
  const v = [];
  const vn = [];
  const f = [];

  // generar vértices de piso y techo
  const bottomVertices = [];
  const topVertices = [];

  for (let i = 0; i < sides; i++) {
    const angulo = (i / sides) * 2 * Math.PI;
    const cos = Math.cos(angulo);
    const sin = Math.sin(angulo);

    // vértice inferior (base Y=0 y radio: r1)
    const x_bot = r1 * cos;
    const z_bot = r1 * sin;
    bottomVertices.push(V3.create(x_bot, 0, z_bot));
    v.push(`v ${fmt(x_bot)} ${fmt(0)} ${fmt(z_bot)}`);

    // vértice superior (altura h y radio r2)
    const x_top = r2 * cos;
    const z_top = r2 * sin;
    topVertices.push(V3.create(x_top, h, z_top));
    v.push(`v ${fmt(x_top)} ${fmt(h)} ${fmt(z_top)}`);
  }

  // reorganizamos para tener bottom consecutivo, luego top consecutivo
  const vReorganized = [];
  for (let i = 0; i < sides; i++) {
    vReorganized.push(v[i * 2]); // bottom
  }
  for (let i = 0; i < sides; i++) {
    vReorganized.push(v[i * 2 + 1]); // top
  }

  // vértices centrales
  const centerBotIndex = 2 * sides + 1;
  vReorganized.push(`v ${fmt(0)} ${fmt(0)} ${fmt(0)}`);

  const centerTopIndex = 2 * sides + 2;
  vReorganized.push(`v ${fmt(0)} ${fmt(h)} ${fmt(0)}`);

  // calcular normales por cara para las paredes laterales
  for (let i = 0; i < sides; i++) {
    const j = (i + 1) % sides; // módulo para conectar último con primer vértice

    const Bi = bottomVertices[i];
    const Ti = topVertices[i];
    const Bj = bottomVertices[j];

    // vectores del lado
    const A = V3.subtract(Ti, Bi); // bottom a top
    const B = V3.subtract(Bj, Bi); // bottom actual a siguiente

    // normal de la cara
    const n = V3.normalize(V3.cross(A, B));
    vn.push(`vn ${fmt(n[0])} ${fmt(n[1])} ${fmt(n[2])}`);
  }

  // caras laterales (2 triángulos por cara, misma normal)
  for (let i = 0; i < sides; i++) {
    const j = (i + 1) % sides;

    // índices de vértices
    const viB = 1 + i; // bottom i
    const vjB = 1 + j; // bottom j
    const viT = sides + 1 + i; // top i
    const vjT = sides + 1 + j; // top j

    const vn_idx = 1 + i; // normal para esta cara

    // triángulo 1: Bi, Ti, Bj (contrarreloj desde afuera)
    f.push(`f ${viB}//${vn_idx} ${viT}//${vn_idx} ${vjB}//${vn_idx}`);

    // triángulo 2: Bj, Ti, Tj (contrarreloj desde afuera)
    f.push(`f ${vjB}//${vn_idx} ${viT}//${vn_idx} ${vjT}//${vn_idx}`);
  }

  // techo: normal (0, 1, 0)
  for (let i = 0; i < sides; i++) {
    const current = sides + 1 + i;
    const next = sides + 1 + ((i + 1) % sides);

    vn.push(`vn ${fmt(0)} ${fmt(1)} ${fmt(0)}`);
    const vn_idx = vn.length;

    f.push(
      `f ${centerTopIndex}//${vn_idx} ${next}//${vn_idx} ${current}//${vn_idx}`
    );
  }

  // piso: normal (0, -1, 0)
  for (let i = 0; i < sides; i++) {
    const current = 1 + i;
    const next = 1 + ((i + 1) % sides);

    vn.push(`vn ${fmt(0)} ${fmt(-1)} ${fmt(0)}`);
    const vn_idx = vn.length;

    f.push(
      `f ${centerBotIndex}//${vn_idx} ${current}//${vn_idx} ${next}//${vn_idx}`
    );
  }

  // escritura de archivo formato obj
  const header = `# OBJ file building_${sides}_${h}_${r1}_${r2}.obj
# sides: ${sides}, h: ${h}, R_Base: ${r1}, R_Cima: ${r2}
# Vertices totales: ${vReorganized.length}
# Normales totales: ${vn.length}
# Caras totales: ${f.length}
`;

  const contenido = [header, ...vReorganized, ...vn, ...f].join("\n");
  const nombre_archivo = `building_${sides}_${h}_${r1}_${r2}.obj`;

  fs.writeFile(nombre_archivo, contenido, (err) => {
    if (err) {
      console.error("Error al escribir el archivo:", err);
    } else {
      console.log(`Wrote ${nombre_archivo}`);
    }
  });
}

main();
