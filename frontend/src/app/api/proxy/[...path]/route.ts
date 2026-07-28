import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 30;

const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000";

async function proxyRequest(req: NextRequest, path: string[]) {
  const targetPath = path.join("/");
  const url = new URL(req.url);
  const targetUrl = `${BACKEND}/${targetPath}${url.search}`;

  const headers = new Headers();
  req.headers.forEach((value, key) => {
    if (key.toLowerCase() === "host") return;
    headers.set(key, value);
  });

  const init: RequestInit = {
    method: req.method,
    headers,
    redirect: "follow",
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.arrayBuffer();
  }

  try {
    const res = await fetch(targetUrl, init);
    const resHeaders = new Headers();
    res.headers.forEach((value, key) => {
      if (["content-encoding", "transfer-encoding"].includes(key.toLowerCase())) return;
      resHeaders.set(key, value);
    });
    return new NextResponse(res.body, { status: res.status, statusText: res.statusText, headers: resHeaders });
  } catch (err) {
    console.error("Proxy error:", targetUrl, err);
    return NextResponse.json({ detail: "Proxy failed to reach backend" }, { status: 502 });
  }
}

export async function GET(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyRequest(req, path);
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyRequest(req, path);
}

export async function PUT(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyRequest(req, path);
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyRequest(req, path);
}
