let activeMenuClose = null;

/** @param {() => void} close */
export function registerOpenShareMenu(close) {
  if (activeMenuClose && activeMenuClose !== close) {
    activeMenuClose();
  }
  activeMenuClose = close;
}

/** @param {() => void} close */
export function unregisterShareMenu(close) {
  if (activeMenuClose === close) {
    activeMenuClose = null;
  }
}

export const SHARE_OPTIONS = [
  { id: "copy", label: "Copiar texto", icon: "icn-copy" },
  { id: "whatsapp", label: "WhatsApp", icon: "icn-whatsapp" },
  { id: "x", label: "X", icon: "icn-x" },
  { id: "facebook", label: "Facebook", icon: "icn-facebook" },
];
