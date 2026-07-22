/** Client-side image compression before meal-photo chat upload. */

const MAX_EDGE = 1280;
const JPEG_QUALITY = 0.72;

export type CompressedImage = {
  base64: string;
  mime: string;
  previewUrl: string;
  width: number;
  height: number;
};

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Could not read image"));
    };
    img.src = url;
  });
}

/** Resize + JPEG-encode; returns raw base64 (no data: prefix) + object URL preview. */
export async function compressImageForChat(file: File): Promise<CompressedImage> {
  if (!file.type.startsWith("image/")) {
    throw new Error("Please choose an image file");
  }
  const img = await loadImage(file);
  const scale = Math.min(1, MAX_EDGE / Math.max(img.width, img.height));
  const width = Math.max(1, Math.round(img.width * scale));
  const height = Math.max(1, Math.round(img.height * scale));
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Canvas unavailable");
  ctx.drawImage(img, 0, 0, width, height);
  const dataUrl = canvas.toDataURL("image/jpeg", JPEG_QUALITY);
  const base64 = dataUrl.split(",", 2)[1] || "";
  if (!base64) throw new Error("Compression failed");
  return {
    base64,
    mime: "image/jpeg",
    previewUrl: dataUrl,
    width,
    height,
  };
}
