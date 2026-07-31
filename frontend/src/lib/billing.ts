import { CheckoutResponse } from "./api";

// PayHere's checkout expects a form POST of hidden fields (including a signed hash) rather
// than a plain link, so a "post" session builds and submits an invisible form instead of
// just navigating. Mock and Stripe checkout sessions are plain "get" redirects.
export function redirectToCheckout(session: CheckoutResponse) {
  if (session.method === "get") {
    window.location.href = session.redirect_url;
    return;
  }

  const form = document.createElement("form");
  form.method = "POST";
  form.action = session.redirect_url;
  for (const [key, value] of Object.entries(session.fields)) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = key;
    input.value = value;
    form.appendChild(input);
  }
  document.body.appendChild(form);
  form.submit();
}
