import { useCallback, useEffect, useId, useRef, useState } from "react";
import { Icon } from "./Icons";
import {
  copyToClipboard,
  shareFacebook,
  shareWhatsApp,
  shareX,
} from "../utils/share";
import {
  SHARE_OPTIONS,
  registerOpenShareMenu,
  unregisterShareMenu,
} from "../utils/shareMenu";

/**
 * @param {{ text: string; compact?: boolean; label?: string }} props
 */
export function ShareMenu({ text, compact = false, label = "Compartir" }) {
  const menuId = useId();
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);
  const closeRef = useRef(() => setOpen(false));

  closeRef.current = () => setOpen(false);

  const closeMenu = useCallback(() => {
    setOpen(false);
    unregisterShareMenu(closeRef.current);
  }, []);

  const openMenu = useCallback(() => {
    registerOpenShareMenu(closeRef.current);
    setOpen(true);
  }, []);

  const toggleMenu = useCallback(
    (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (open) {
        closeMenu();
      } else {
        openMenu();
      }
    },
    [open, closeMenu, openMenu],
  );

  useEffect(() => {
    if (!open) return;

    function handleClick(event) {
      if (!wrapRef.current?.contains(event.target)) {
        closeMenu();
      }
    }

    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, [open, closeMenu]);

  useEffect(() => {
    return () => unregisterShareMenu(closeRef.current);
  }, []);

  function handleAction(actionId) {
    if (actionId === "copy") copyToClipboard(text);
    if (actionId === "whatsapp") shareWhatsApp(text);
    if (actionId === "x") shareX(text);
    if (actionId === "facebook") shareFacebook();
    closeMenu();
  }

  return (
    <span
      className={`share-wrap${open ? " share-wrap-open" : ""}`}
      ref={wrapRef}
      data-share-menu={menuId}
    >
      {compact ? (
        <button
          type="button"
          className="icon-btn-sm"
          title="Compartir"
          aria-label="Compartir cita"
          aria-haspopup="menu"
          aria-expanded={open}
          onClick={toggleMenu}
        >
          <Icon id="icn-share" size={14} />
        </button>
      ) : (
        <button
          type="button"
          className="icon-btn"
          aria-label="Compartir respuesta"
          aria-haspopup="menu"
          aria-expanded={open}
          onClick={toggleMenu}
        >
          <Icon id="icn-share" />
          {label}
        </button>
      )}

      <div
        className={`share-menu${open ? " open" : ""}${compact ? " share-menu-compact" : ""}`}
        role="menu"
        aria-hidden={!open}
      >
        {SHARE_OPTIONS.map((option) => (
          <button
            key={option.id}
            type="button"
            className="share-item"
            role="menuitem"
            onClick={(event) => {
              event.preventDefault();
              event.stopPropagation();
              handleAction(option.id);
            }}
          >
            <Icon id={option.icon} /> {option.label}
          </button>
        ))}
      </div>
    </span>
  );
}
