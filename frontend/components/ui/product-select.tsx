import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useEffect, useState } from "react"

type Product = {
  id: string
  name: string
}

interface ProductSelectProps {
  onValueChange: (value: string) => void;
}

export function ProductSelect({ onValueChange }: ProductSelectProps) {
  const [items, setItems] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    async function fetchItems() {
      try {
        const res = await fetch("http://localhost:8000/product")
        if (!res.ok) throw new Error("Failed to fetch")
        const data: Product[] = await res.json()
        setItems(data)
      } catch (err) {
        console.error("Failed to fetch products, using mock data", err)
        setItems([
          { id: "1", name: "Mock Product 1" },
          { id: "2", name: "Mock Product 2" },
          { id: "3", name: "Mock Product 3" },
        ])
      } finally {
        setLoading(false)
      }
    }

    fetchItems()
  }, [])

  if (!mounted) return null;

  return (
    <Select disabled={loading} onValueChange={onValueChange}>
      <SelectTrigger className="w-full max-w-48">
        <SelectValue placeholder={loading ? "Loading..." : "Select a product"} />
      </SelectTrigger>

      <SelectContent>
        <SelectGroup>
          <SelectLabel>Products</SelectLabel>
          {items.map(({ id, name }) => (
            <SelectItem key={id} value={id}>
              {name}
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </Select>
  )
}
