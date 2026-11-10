// CliniqPay flow atlas. Rebuild with node docs/app-map/build-atlas.mjs.
export const meta = {
  "title": "CliniqPay · Flow Atlas",
  "slug": "cliniqpay",
  "date": "2026-11-08",
  "commit": "initial plan (nothing built yet)",
  "scope": "Plan a lightweight billing and cashier desk for small healthcare providers in India.",
  "groups": [
    "Start here",
    "Features",
    "Systems",
    "Supporting pages"
  ],
  "featureGroup": "Features",
  "buildOrder": [
    "enrollment",
    "platform-admin",
    "setup",
    "billing",
    "payment",
    "summary",
    "receipts",
    "release"
  ],
  "platforms": [
    "web"
  ]
};

export const graphs = [
  {
    "id": "overview",
    "group": "Start here",
    "title": "The whole product",
    "status": "planned",
    "subtitle": "Hospital enrollment, platform administration, billing and collections for healthcare providers in India.",
    "source": "",
    "rows": [
      [
        [
          "open",
          "Open CliniqPay",
          "Staff start at the cashier desk"
        ]
      ],
      [
        [
          "f-setup",
          "Hospital setup",
          "Open the hospital setup flow"
        ]
      ],
      [
        [
          "f-billing",
          "Quick billing",
          "Open the quick billing flow"
        ]
      ],
      [
        [
          "f-payment",
          "Payment collection",
          "Open the payment collection flow"
        ]
      ],
      [
        [
          "f-receipts",
          "WhatsApp receipts",
          "Open the whatsapp receipts flow"
        ]
      ],
      [
        [
          "f-summary",
          "Daily summary",
          "Open the daily summary flow"
        ]
      ],
      [
        [
          "f-enrollment",
          "Hospital enrollment",
          "Open the hospital enrollment flow"
        ]
      ],
      [
        [
          "f-platform-admin",
          "CliniqPay master administration",
          "Open the cliniqpay master administration flow"
        ]
      ],
      [
        [
          "outcome",
          "Daily cashier workflow",
          "Bills, collections, receipts and summaries"
        ]
      ]
    ],
    "edges": [
      [
        "open",
        "f-setup",
        "Choose"
      ],
      [
        "f-setup",
        "outcome",
        "Supports"
      ],
      [
        "open",
        "f-billing",
        "Choose"
      ],
      [
        "f-billing",
        "outcome",
        "Supports"
      ],
      [
        "open",
        "f-payment",
        "Choose"
      ],
      [
        "f-payment",
        "outcome",
        "Supports"
      ],
      [
        "open",
        "f-receipts",
        "Choose"
      ],
      [
        "f-receipts",
        "outcome",
        "Supports"
      ],
      [
        "open",
        "f-summary",
        "Choose"
      ],
      [
        "f-summary",
        "outcome",
        "Supports"
      ],
      [
        "open",
        "f-enrollment",
        "Choose"
      ],
      [
        "f-enrollment",
        "outcome",
        "Supports"
      ],
      [
        "open",
        "f-platform-admin",
        "Choose"
      ],
      [
        "f-platform-admin",
        "outcome",
        "Supports"
      ]
    ],
    "drilldowns": {
      "f-setup": "setup",
      "f-billing": "billing",
      "f-payment": "payment",
      "f-receipts": "receipts",
      "f-summary": "summary",
      "f-enrollment": "enrollment",
      "f-platform-admin": "platform-admin"
    },
    "notes": [
      "Planned from requirement.md; integration and implementation decisions remain open."
    ]
  },
  {
    "id": "roadmap",
    "group": "Start here",
    "title": "Build order",
    "status": "planned",
    "subtitle": "The order Loop builds the features in (meta.buildOrder).",
    "source": "",
    "rows": [
      [
        [
          "r-enrollment",
          "Hospital enrollment",
          "Track: .loop/tracks/enrollment/spec.md"
        ]
      ],
      [
        [
          "r-platform-admin",
          "CliniqPay master administration",
          "Track: .loop/tracks/platform-admin/spec.md"
        ]
      ],
      [
        [
          "r-setup",
          "Hospital setup",
          "Track: .loop/tracks/setup/spec.md"
        ]
      ],
      [
        [
          "r-billing",
          "Quick billing",
          "Track: .loop/tracks/billing/spec.md"
        ]
      ],
      [
        [
          "r-payment",
          "Payment collection",
          "Track: .loop/tracks/payment/spec.md"
        ]
      ],
      [
        [
          "r-receipts",
          "WhatsApp receipts",
          "Track: .loop/tracks/receipts/spec.md"
        ]
      ],
      [
        [
          "r-summary",
          "Daily summary",
          "Track: .loop/tracks/summary/spec.md"
        ]
      ]
    ],
    "edges": [],
    "drilldowns": {
      "r-setup": "setup",
      "r-billing": "billing",
      "r-payment": "payment",
      "r-receipts": "receipts",
      "r-summary": "summary",
      "r-platform-admin": "platform-admin",
      "r-enrollment": "enrollment"
    },
    "notes": [
      "npm run atlas:next always names the first map in this order that is not delivered. The release map comes last."
    ]
  },
  {
    "id": "enrollment",
    "group": "Features",
    "title": "Hospital enrollment",
    "status": "delivered",
    "dependsOn": [],
    "blockedBy": "",
    "subtitle": "Landing page hospital enrollment and status tracking.",
    "source": "enrollment/views.py:7; enrollment/tests.py:6",
    "rows": [
      [
        [
          "s1",
          "Visit the CliniqPay landing page",
          "Hospital representative visits the landing page and initiates enrollment."
        ]
      ],
      [
        [
          "s2",
          "Enter hospital and administrator details",
          "Form collects hospital name, city, state, contact phone, email, and admin name."
        ]
      ],
      [
        [
          "s3",
          "Submit enrollment and receive confirmation",
          "Submission is validated, saved with status pending_review, and reference token issued."
        ]
      ],
      [
        [
          "s4",
          "Track review or activation status",
          "Hospital checks activation status using their reference token or email."
        ]
      ]
    ],
    "edges": [
      [
        "s1",
        "s2",
        "Next"
      ],
      [
        "s2",
        "s3",
        "Submit"
      ],
      [
        "s3",
        "s4",
        "Track"
      ]
    ],
    "notes": [
      "Track: .loop/tracks/enrollment/spec.md"
    ]
  },
  {
    "id": "platform-admin",
    "group": "Features",
    "title": "CliniqPay master administration",
    "status": "delivered",
    "dependsOn": [
      "enrollment"
    ],
    "blockedBy": "",
    "subtitle": "Review, approve, and activate enrolled hospital accounts.",
    "source": "platform_admin/views.py:9; platform_admin/tests.py:6",
    "rows": [
      [
        [
          "s1",
          "Sign in as an authorized platform administrator",
          "Master administrator signs into the platform administration console."
        ]
      ],
      [
        [
          "s2",
          "Review enrolled hospitals and enrollment requests",
          "List pending and active clinic registrations with contact and applicant details."
        ]
      ],
      [
        [
          "s3",
          "View and manage hospital account status",
          "Approve request, issue 7-day trial, provision clinic workspace, or reject application."
        ]
      ],
      [
        [
          "s4",
          "Review administrative actions and audit history",
          "Track who approved each clinic, timestamps, and audit history."
        ]
      ]
    ],
    "edges": [
      [
        "s1",
        "s2",
        "Next"
      ],
      [
        "s2",
        "s3",
        "Action"
      ],
      [
        "s3",
        "s4",
        "Audit"
      ]
    ],
    "notes": [
      "Track: .loop/tracks/platform-admin/spec.md"
    ]
  },
  {
    "id": "setup",
    "group": "Features",
    "title": "Hospital setup",
    "status": "delivered",
    "dependsOn": [
      "enrollment",
      "platform-admin"
    ],
    "blockedBy": "",
    "subtitle": "Configure hospital details, tariffs, doctors, and payment settings.",
    "source": "setup_hospital/views.py:16; setup_hospital/tests.py:7",
    "rows": [
      [
        [
          "s1",
          "Enter hospital details, room ranges and billing preferences",
          "Set hospital name, GSTIN, bed count, starting room number, validate zero-overlap room allocations, and 8 PM daily closing time."
        ]
      ],
      [
        [
          "s2",
          "Configure services, tariffs and applicable tax",
          "Add or edit procedures (OPD Consultation, ECG, Room Rent) and tax rates."
        ]
      ],
      [
        [
          "s3",
          "Configure medical staff & tariff agreements",
          "Add physicians with professional fee splits, clinical login credentials, and payment settings."
        ]
      ],
      [
        [
          "s4",
          "Review and save settings",
          "Validate setup completeness and prepare cashier desk for live billing."
        ]
      ]
    ],
    "edges": [
      [
        "s1",
        "s2",
        "Next"
      ],
      [
        "s2",
        "s3",
        "Next"
      ],
      [
        "s3",
        "s4",
        "Save"
      ]
    ],
    "notes": [
      "Track: .loop/tracks/setup/spec.md"
    ]
  },
  {
    "id": "billing",
    "group": "Features",
    "title": "Quick billing",
    "status": "delivered",
    "dependsOn": [
      "setup"
    ],
    "blockedBy": "",
    "subtitle": "10-second OPD and IPD billing with serial auto-increment, dedicated Pharmacist terminal with mandatory batch and expiry tracking, inward batch CSV import, and storage rack coordinates.",
    "source": "billing/views.py:10; billing/tests.py:8",
    "rows": [
      [
        [
          "s1",
          "Find or enter patient details",
          "Define validation, failure and recovery before implementation."
        ]
      ],
      [
        [
          "s2",
          "Select services and quantities",
          "Define validation, failure and recovery before implementation."
        ]
      ],
      [
        [
          "s3",
          "Review itemized charges and applicable tax",
          "Define validation, failure and recovery before implementation."
        ]
      ],
      [
        [
          "s4",
          "Create bill and show amount due",
          "Define validation, failure and recovery before implementation."
        ]
      ]
    ],
    "edges": [
      [
        "s1",
        "s2",
        "Next"
      ],
      [
        "s2",
        "s3",
        "Next"
      ],
      [
        "s3",
        "s4",
        "Next"
      ]
    ],
    "notes": [
      "Track: .loop/tracks/billing/spec.md"
    ]
  },
  {
    "id": "payment",
    "group": "Features",
    "title": "Payment collection",
    "status": "delivered",
    "dependsOn": [
      "billing"
    ],
    "blockedBy": "",
    "subtitle": "Collect payment via exact-amount dynamic UPI QR or verified cash.",
    "source": "payments/views.py:12; payments/tests.py:9",
    "rows": [
      [
        [
          "s1",
          "Open an outstanding bill",
          "Open the unpaid invoice to collect settlement."
        ]
      ],
      [
        [
          "s2",
          "Choose cash or exact-amount UPI QR",
          "Present on-screen dynamic UPI QR with embedded amount or select Cash entry."
        ]
      ],
      [
        [
          "s3",
          "Verify payment or explicitly record cash",
          "Receive automated UPI webhook match or record cashier-verified physical cash."
        ]
      ],
      [
        [
          "s4",
          "Show confirmed, pending or failed status",
          "Mark bill paid, generate receipt token, and unlock WhatsApp dispatch."
        ]
      ]
    ],
    "edges": [
      [
        "s1",
        "s2",
        "Next"
      ],
      [
        "s2",
        "s3",
        "Next"
      ],
      [
        "s3",
        "s4",
        "Confirm"
      ]
    ],
    "notes": [
      "Track: .loop/tracks/payment/spec.md"
    ]
  },
  {
    "id": "receipts",
    "group": "Features",
    "title": "WhatsApp receipts",
    "status": "delivered",
    "dependsOn": [
      "billing",
      "payment"
    ],
    "blockedBy": "",
    "subtitle": "Planned whatsapp receipts workflow.",
    "source": "receipts/views.py:10",
    "rows": [
      [
        [
          "s1",
          "Open bill and payment receipt",
          "Define validation, failure and recovery before implementation."
        ]
      ],
      [
        [
          "s2",
          "Confirm recipient number and receipt details",
          "Define validation, failure and recovery before implementation."
        ]
      ],
      [
        [
          "s3",
          "Send through a WhatsApp provider",
          "Define validation, failure and recovery before implementation."
        ]
      ],
      [
        [
          "s4",
          "Show delivery status or failure and retry",
          "Define validation, failure and recovery before implementation."
        ]
      ]
    ],
    "edges": [
      [
        "s1",
        "s2",
        "Next"
      ],
      [
        "s2",
        "s3",
        "Next"
      ],
      [
        "s3",
        "s4",
        "Next"
      ]
    ],
    "notes": [
      "Track: .loop/tracks/receipts/spec.md"
    ]
  },
  {
    "id": "summary",
    "group": "Features",
    "title": "Daily summary",
    "status": "delivered",
    "dependsOn": [
      "billing",
      "payment"
    ],
    "blockedBy": "",
    "subtitle": "Daily 8 PM collections, doctor shares & reconciliation report.",
    "source": "summary/views.py:12",
    "rows": [
      [
        [
          "s1",
          "Choose reporting date",
          "Define validation, failure and recovery before implementation."
        ]
      ],
      [
        [
          "s2",
          "Review cash, UPI and outstanding balances",
          "Define validation, failure and recovery before implementation."
        ]
      ],
      [
        [
          "s3",
          "Review doctor shares",
          "Define validation, failure and recovery before implementation."
        ]
      ],
      [
        [
          "s4",
          "Schedule or send summary through WhatsApp",
          "Define validation, failure and recovery before implementation."
        ]
      ]
    ],
    "edges": [
      [
        "s1",
        "s2",
        "Next"
      ],
      [
        "s2",
        "s3",
        "Next"
      ],
      [
        "s3",
        "s4",
        "Next"
      ]
    ],
    "notes": [
      "Track: .loop/tracks/summary/spec.md"
    ]
  },
  {
    "id": "quality-gates",
    "group": "Systems",
    "title": "How every feature is built",
    "status": "delivered",
    "subtitle": "The atlas-first checkpoint loop this project follows.",
    "source": "AGENTS.md:1; .loop/workflow.md:1; .loop/platform.md:1",
    "rows": [
      [
        [
          "next",
          "Pick next map",
          "npm run atlas:next names the next planned map and its track."
        ]
      ],
      [
        [
          "map",
          "Make the map exact",
          "Steps, branches, defaults, failure paths. Status: building."
        ]
      ],
      [
        [
          "build",
          "Build to the map",
          "Smallest coherent change, all languages, version bump. Platform: Django web application for desktop and tablet browsers."
        ]
      ],
      [
        [
          "check",
          "Prove it",
          "Behaviour tests (Django tests or pytest once configured), npm run atlas, phone/tablet and desktop browser checks once configured. Proof ladder in .loop/platform.md."
        ]
      ],
      [
        [
          "legal",
          "Legal rows",
          "Update .loop/legal-checklist.md rows this change touches (data, cookies, APIs, packages, assets, AI content, payments, advice, claims). Rules: Loop/LEGAL-CHECKLIST.md."
        ]
      ],
      [
        [
          "flip",
          "Flip to delivered",
          "Add source refs (file:line). The build refuses delivered without source."
        ]
      ],
      [
        [
          "record",
          "Record and report",
          "Track, fix queue, HANDOFF CURRENT RESUME, commit, plain-words report."
        ]
      ]
    ],
    "edges": [
      [
        "next",
        "map",
        "Read"
      ],
      [
        "map",
        "build",
        "Exact"
      ],
      [
        "build",
        "check",
        "Done"
      ],
      [
        "check",
        "build",
        "Fails"
      ],
      [
        "check",
        "legal",
        "Passes"
      ],
      [
        "legal",
        "build",
        "Gap"
      ],
      [
        "legal",
        "flip",
        "Clear"
      ],
      [
        "flip",
        "record",
        "Built"
      ],
      [
        "record",
        "next",
        "Repeat"
      ]
    ],
    "notes": [
      "Defined by AGENTS.md, .loop/workflow.md and .loop/platform.md (generated by Loop)."
    ]
  },
  {
    "id": "release",
    "group": "Systems",
    "title": "Release",
    "status": "planned",
    "subtitle": "How CliniqPay reaches users on Django web application for desktop and tablet browsers.",
    "source": "",
    "rows": [
      [
        [
          "legal-audit",
          "Final legal audit",
          "Legal check 20: recheck all 20 rows in .loop/legal-checklist.md, flag lawyer items, owner approves legal pages. Rules: Loop/LEGAL-CHECKLIST.md."
        ]
      ],
      [
        [
          "p1",
          "Build or bundle the site",
          "Release step: Build or bundle the site. Owner approval gates in Loop/loop.md apply."
        ]
      ],
      [
        [
          "p2",
          "Check it on a phone browser",
          "Release step: Check it on a phone browser. Owner approval gates in Loop/loop.md apply."
        ]
      ],
      [
        [
          "p3",
          "Owner approves the deploy",
          "Release step: Owner approves the deploy. Owner approval gates in Loop/loop.md apply."
        ]
      ],
      [
        [
          "p4",
          "Deploy to the host",
          "Release step: Deploy to the host. Owner approval gates in Loop/loop.md apply."
        ]
      ],
      [
        [
          "p5",
          "Confirm the live version number",
          "Release step: Confirm the live version number. Owner approval gates in Loop/loop.md apply."
        ]
      ]
    ],
    "edges": [
      [
        "legal-audit",
        "p1",
        "Then"
      ],
      [
        "p1",
        "p2",
        "Then"
      ],
      [
        "p2",
        "p3",
        "Then"
      ],
      [
        "p3",
        "p4",
        "Then"
      ],
      [
        "p4",
        "p5",
        "Then"
      ]
    ],
    "notes": [
      "Built last, after the first-release features. Track: .loop/tracks/release/spec.md"
    ]
  }
];
