"use client";

import { useEffect, useRef } from "react";
import { Bold, Heading3, Italic, List, ListOrdered, Underline } from "lucide-react";

const toolbarBtn =
  "rounded-md p-1.5 text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800";

export default function RichTextEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (html: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const initialized = useRef(false);

  // Only seed the contentEditable's innerHTML once — re-syncing it on every `value` change
  // (from onChange -> parent state -> back down as a prop) would reset the caret position on
  // every keystroke.
  useEffect(() => {
    if (ref.current && !initialized.current) {
      ref.current.innerHTML = value;
      initialized.current = true;
    }
  }, [value]);

  function exec(command: string, arg?: string) {
    ref.current?.focus();
    document.execCommand(command, false, arg);
    onChange(ref.current?.innerHTML || "");
  }

  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800">
      <div className="flex flex-wrap gap-1 border-b border-zinc-200 p-1.5 dark:border-zinc-800">
        <button type="button" className={toolbarBtn} onMouseDown={(e) => e.preventDefault()} onClick={() => exec("bold")} aria-label="Bold">
          <Bold className="h-4 w-4" />
        </button>
        <button type="button" className={toolbarBtn} onMouseDown={(e) => e.preventDefault()} onClick={() => exec("italic")} aria-label="Italic">
          <Italic className="h-4 w-4" />
        </button>
        <button type="button" className={toolbarBtn} onMouseDown={(e) => e.preventDefault()} onClick={() => exec("underline")} aria-label="Underline">
          <Underline className="h-4 w-4" />
        </button>
        <button
          type="button"
          className={toolbarBtn}
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => exec("formatBlock", "h3")}
          aria-label="Heading"
        >
          <Heading3 className="h-4 w-4" />
        </button>
        <button
          type="button"
          className={toolbarBtn}
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => exec("insertUnorderedList")}
          aria-label="Bullet list"
        >
          <List className="h-4 w-4" />
        </button>
        <button
          type="button"
          className={toolbarBtn}
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => exec("insertOrderedList")}
          aria-label="Numbered list"
        >
          <ListOrdered className="h-4 w-4" />
        </button>
      </div>
      <div
        ref={ref}
        contentEditable
        suppressContentEditableWarning
        onInput={() => onChange(ref.current?.innerHTML || "")}
        className="min-h-[280px] max-h-[45vh] overflow-y-auto bg-white p-5 font-serif text-sm leading-relaxed text-zinc-900 focus:outline-none dark:bg-zinc-950 dark:text-zinc-100 [&_h3]:mt-3 [&_h3]:mb-1.5 [&_h3]:text-base [&_h3]:font-bold [&_p]:mb-2 [&_ul]:mb-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:mb-2 [&_ol]:list-decimal [&_ol]:pl-5 [&_li]:mb-1"
      />
    </div>
  );
}
