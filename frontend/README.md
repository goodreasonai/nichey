# Frontend Development

The frontend is distributed with the package as a static bundle from Next.js. 

To run the frontend for development, you'll need `npm`. To run the development server, you'll need to have a wiki being served (by using `Wiki().serve`) at port 5000. The frontend dev server is run on port 3000 (the frontend accompanying the backend at port 5000 won't be up to date until you build).

The dev frontend can be started with `npm run dev` or `next run dev`. You may need to run `npm install` beforehand.

To build the frontend so that it's run with the package at port 5000, use `./build.sh`. That runs `npm run build` and then renames the resulting `out` folder as `../wiki/static`, placing it into the Python package. Before any PR, you must use `./build.sh` first so that the build version in `../wiki/static` matches what's here in `frontend`.

## How this was made

This folder was bootstrapped with `create-next-app`. These options were used:

```
TypeScript: No
ESLint: No
Tailwind CSS: No
src/ directory: Yes
App Router: Yes
Turbopack: Yes
Custom alias: No
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.js`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!
