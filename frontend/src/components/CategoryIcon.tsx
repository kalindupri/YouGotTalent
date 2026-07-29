import { createElement } from "react";
import { categoryIcon } from "@/lib/ui";

export default function CategoryIcon({ category, className }: { category: string; className?: string }) {
  return createElement(categoryIcon(category), { className });
}
