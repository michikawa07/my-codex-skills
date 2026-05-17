use serde::Serialize;
use std::collections::{BTreeMap, HashSet};
use std::env;
use std::fs;
use std::path::PathBuf;
use typst_syntax::{parse, SyntaxKind, SyntaxNode};

#[derive(Serialize)]
struct Item {
    id: String,
    source: &'static str,
    kind: String,
    line: usize,
    end_line: usize,
    start: usize,
    end: usize,
    text: String,
    raw: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    comments_inside: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    syntax_kind: Option<String>,
}

#[derive(Serialize)]
struct Output {
    schema: &'static str,
    source: String,
    parser: &'static str,
    items: Vec<Item>,
    summary: BTreeMap<String, usize>,
    parse_errors: Vec<String>,
}

fn main() {
    let mut args = env::args().skip(1);
    let source_path = match args.next() {
        Some(path) => PathBuf::from(path),
        None => {
            eprintln!("usage: typst_ast_scanner <source.typ> [--output out.json]");
            std::process::exit(2);
        }
    };

    let mut output_path: Option<PathBuf> = None;
    while let Some(arg) = args.next() {
        if arg == "--output" {
            output_path = args.next().map(PathBuf::from);
        } else {
            eprintln!("unknown argument: {arg}");
            std::process::exit(2);
        }
    }

    let source = fs::read_to_string(&source_path).unwrap_or_else(|err| {
        eprintln!("failed to read {}: {err}", source_path.display());
        std::process::exit(1);
    });
    let line_starts = line_starts(&source);
    let root = parse(&source);
    let mut items = Vec::new();
    let mut caption_starts = HashSet::new();
    visit(
        &root,
        0,
        &source,
        &line_starts,
        &mut items,
        &mut caption_starts,
    );

    let mut summary = BTreeMap::new();
    for item in &items {
        *summary.entry(item.kind.clone()).or_insert(0) += 1;
    }

    let output = Output {
        schema: "typst-to-tex-source-scan-v2",
        source: source_path.to_string_lossy().to_string(),
        parser: "typst-syntax",
        items,
        summary,
        parse_errors: root
            .errors()
            .into_iter()
            .map(|err| err.message.to_string())
            .collect(),
    };

    let json = serde_json::to_string_pretty(&output).expect("serialize output");
    if let Some(path) = output_path {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).unwrap_or_else(|err| {
                eprintln!("failed to create {}: {err}", parent.display());
                std::process::exit(1);
            });
        }
        fs::write(&path, format!("{json}\n")).unwrap_or_else(|err| {
            eprintln!("failed to write {}: {err}", path.display());
            std::process::exit(1);
        });
        println!("source_scan={}", path.display());
        println!("items={}", output.summary.values().sum::<usize>());
    } else {
        println!("{json}");
    }
}

fn visit(
    node: &SyntaxNode,
    start: usize,
    source: &str,
    line_starts: &[usize],
    items: &mut Vec<Item>,
    caption_starts: &mut HashSet<usize>,
) {
    let end = start + node.len();
    collect_item(node, start, end, source, line_starts, items, caption_starts);

    let mut child_start = start;
    for child in node.children() {
        visit(
            child,
            child_start,
            source,
            line_starts,
            items,
            caption_starts,
        );
        child_start += child.len();
    }
}

fn collect_item(
    node: &SyntaxNode,
    start: usize,
    end: usize,
    source: &str,
    line_starts: &[usize],
    items: &mut Vec<Item>,
    caption_starts: &mut HashSet<usize>,
) {
    match node.kind() {
        SyntaxKind::LineComment => {
            let raw = raw_text(source, start, end).to_string();
            let text = raw.trim_start_matches("//").trim().to_string();
            if !text.is_empty() {
                push_item(
                    items,
                    "comment",
                    start,
                    end,
                    source,
                    line_starts,
                    text,
                    None,
                    None,
                    node.kind(),
                );
            }
        }
        SyntaxKind::BlockComment => {
            let raw = raw_text(source, start, end).to_string();
            let text = raw
                .trim_start_matches("/*")
                .trim_end_matches("*/")
                .trim()
                .to_string();
            if !text.is_empty() {
                push_item(
                    items,
                    "comment",
                    start,
                    end,
                    source,
                    line_starts,
                    text,
                    None,
                    None,
                    node.kind(),
                );
            }
        }
        SyntaxKind::Label => {
            let raw = raw_text(source, start, end).to_string();
            let text = raw
                .trim_start_matches('<')
                .trim_end_matches('>')
                .to_string();
            push_item(
                items,
                "label",
                start,
                end,
                source,
                line_starts,
                text,
                None,
                None,
                node.kind(),
            );
        }
        SyntaxKind::Ref => {
            let raw = node.clone().into_text().to_string();
            if let Some(target) = reference_target(&raw) {
                push_item(
                    items,
                    "reference",
                    start,
                    end,
                    source,
                    line_starts,
                    target,
                    None,
                    None,
                    node.kind(),
                );
            }
        }
        SyntaxKind::Heading => {
            let text = node.clone().into_text().to_string();
            let level = text.chars().take_while(|c| *c == '=').count();
            push_item(
                items,
                "heading",
                start,
                end,
                source,
                line_starts,
                text.trim().to_string(),
                Some(format!("level:{level}")),
                None,
                node.kind(),
            );
        }
        SyntaxKind::LetBinding => {
            let (raw_start, raw_end) = include_leading_hash(source, start, end);
            let text = raw_text(source, raw_start, raw_end).trim().to_string();
            let name = first_ident(node);
            push_item(
                items,
                "source_let",
                raw_start,
                raw_end,
                source,
                line_starts,
                text,
                name,
                None,
                node.kind(),
            );
        }
        SyntaxKind::ModuleImport => {
            push_item(
                items,
                "module_import",
                start,
                end,
                source,
                line_starts,
                raw_text(source, start, end).trim().to_string(),
                None,
                None,
                node.kind(),
            );
        }
        SyntaxKind::FuncCall => {
            let Some(name) = function_name(node) else {
                return;
            };
            let (raw_start, raw_end) = include_leading_hash(source, start, end);
            let raw = raw_text(source, raw_start, raw_end).trim().to_string();
            push_item(
                items,
                "active_command",
                raw_start,
                raw_end,
                source,
                line_starts,
                name.clone(),
                Some(name.clone()),
                None,
                node.kind(),
            );

            match name.as_str() {
                "qty" | "unit" => push_item(
                    items,
                    "qty_or_unit",
                    raw_start,
                    raw_end,
                    source,
                    line_starts,
                    raw.clone(),
                    Some(name.clone()),
                    None,
                    node.kind(),
                ),
                "subpar_grid" => push_item(
                    items,
                    "subpar_grid",
                    raw_start,
                    raw_end,
                    source,
                    line_starts,
                    raw.clone(),
                    Some(name.clone()),
                    Some(count_comments(node)),
                    node.kind(),
                ),
                "lnote" | "rnote" => push_item(
                    items,
                    "note",
                    raw_start,
                    raw_end,
                    source,
                    line_starts,
                    raw.clone(),
                    Some(name.clone()),
                    None,
                    node.kind(),
                ),
                "figure" | "table" | "bibliography" => push_item(
                    items,
                    &name,
                    raw_start,
                    raw_end,
                    source,
                    line_starts,
                    raw.clone(),
                    Some(name.clone()),
                    Some(count_comments(node)),
                    node.kind(),
                ),
                _ => {}
            }

            if line_no(raw_start, line_starts) != line_no(raw_end.saturating_sub(1), line_starts) {
                push_item(
                    items,
                    "multiline_command",
                    raw_start,
                    raw_end,
                    source,
                    line_starts,
                    raw,
                    Some(name),
                    Some(count_comments(node)),
                    node.kind(),
                );
            }
        }
        SyntaxKind::Named => {
            if first_ident(node).as_deref() == Some("caption") {
                let raw_start = start;
                let raw_end = end;
                if caption_starts.insert(raw_start) {
                    let kind = if line_no(raw_start, line_starts)
                        == line_no(raw_end.saturating_sub(1), line_starts)
                    {
                        "caption_inline"
                    } else {
                        "caption_block"
                    };
                    push_item(
                        items,
                        kind,
                        raw_start,
                        raw_end,
                        source,
                        line_starts,
                        raw_text(source, raw_start, raw_end).trim().to_string(),
                        Some("caption".to_string()),
                        Some(count_comments(node)),
                        node.kind(),
                    );
                }
            }
        }
        _ => {}
    }
}

fn push_item(
    items: &mut Vec<Item>,
    kind: &str,
    start: usize,
    end: usize,
    source: &str,
    line_starts: &[usize],
    text: String,
    name: Option<String>,
    comments_inside: Option<usize>,
    syntax_kind: SyntaxKind,
) {
    let safe_end = end.min(source.len());
    let line = line_no(start, line_starts);
    let end_line = line_no(safe_end.saturating_sub(1), line_starts);
    items.push(Item {
        id: format!("{kind}:{line}:{start}:{safe_end}"),
        source: "source-ast",
        kind: kind.to_string(),
        line,
        end_line,
        start,
        end: safe_end,
        text,
        raw: raw_text(source, start, safe_end).to_string(),
        name,
        comments_inside,
        syntax_kind: Some(format!("{syntax_kind:?}")),
    });
}

fn function_name(node: &SyntaxNode) -> Option<String> {
    for child in node.children() {
        match child.kind() {
            SyntaxKind::Ident | SyntaxKind::MathIdent => return Some(child.text().to_string()),
            SyntaxKind::FieldAccess => return Some(field_access_text(child)),
            _ => {}
        }
    }
    None
}

fn first_ident(node: &SyntaxNode) -> Option<String> {
    for child in node.children() {
        match child.kind() {
            SyntaxKind::Ident | SyntaxKind::MathIdent => return Some(child.text().to_string()),
            SyntaxKind::FieldAccess => return Some(field_access_text(child)),
            _ => {}
        }
    }
    None
}

fn field_access_text(node: &SyntaxNode) -> String {
    let mut out = String::new();
    collect_field_access_text(node, &mut out);
    out
}

fn collect_field_access_text(node: &SyntaxNode, out: &mut String) {
    match node.kind() {
        SyntaxKind::Ident | SyntaxKind::MathIdent | SyntaxKind::Dot => out.push_str(node.text()),
        _ => {
            for child in node.children() {
                collect_field_access_text(child, out);
            }
        }
    }
}

fn reference_target(raw: &str) -> Option<String> {
    let body = raw.trim().strip_prefix('@')?;
    let mut target = String::new();
    for ch in body.chars() {
        if ch == '[' || ch.is_whitespace() {
            break;
        }
        target.push(ch);
    }
    if target.is_empty() {
        None
    } else {
        Some(target)
    }
}

fn count_comments(node: &SyntaxNode) -> usize {
    let mut count = 0;
    if matches!(
        node.kind(),
        SyntaxKind::LineComment | SyntaxKind::BlockComment
    ) {
        count += 1;
    }
    for child in node.children() {
        count += count_comments(child);
    }
    count
}

fn include_leading_hash(source: &str, start: usize, end: usize) -> (usize, usize) {
    if start > 0 && source.as_bytes().get(start - 1) == Some(&b'#') {
        (start - 1, end)
    } else {
        (start, end)
    }
}

fn raw_text(source: &str, start: usize, end: usize) -> &str {
    source
        .get(start.min(source.len())..end.min(source.len()))
        .unwrap_or("")
}

fn line_starts(source: &str) -> Vec<usize> {
    let mut starts = vec![0];
    for (idx, byte) in source.bytes().enumerate() {
        if byte == b'\n' {
            starts.push(idx + 1);
        }
    }
    starts
}

fn line_no(offset: usize, line_starts: &[usize]) -> usize {
    match line_starts.binary_search(&offset) {
        Ok(index) => index + 1,
        Err(index) => index,
    }
}
