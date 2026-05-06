import "./globals.css";

export const metadata = {
  title: "DHE — Upload data",
  description: "Unggah CSV atau Excel ke API DHE",
};

export default function RootLayout({ children }) {
  return (
    <html lang="id">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        {children}
      </body>
    </html>
  );
}
