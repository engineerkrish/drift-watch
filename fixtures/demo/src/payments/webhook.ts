export function verifyWebhook() {
    const secret = process.env.PAYMENTS_WEBHOOK_SECRET;
    return Boolean(secret);
}
