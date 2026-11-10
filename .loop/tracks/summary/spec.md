# Daily summary

Status: delivered. Source: summary/views.py:12.

## Flow

- Choose reporting date
- Review cash, UPI and outstanding balances
- Review doctor shares
- Schedule or send summary through WhatsApp

## Implementation Details

- **Collections Split:** Direct calculation of settled UPI funds vs register cash-in-hand.
- **Confidential Doctor Cut Engine:** Computes percentage and fixed cuts per doctor across all consultations for the selected reporting date.
- **WhatsApp 8 PM Digest:** One-click dispatch with E.164 formatting to the hospital administrator phone number.
