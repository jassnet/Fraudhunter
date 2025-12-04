import { Separator } from "@/components/ui/separator";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <div className="space-y-6 p-10 pb-16 md:block">
      <div className="space-y-0.5">
        <h2 className="text-2xl font-bold tracking-tight">設定</h2>
        <p className="text-muted-foreground">
          不正検知システムの閾値や動作設定を管理します。
        </p>
      </div>
      <Separator className="my-6" />
      <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
        <div className="flex-1 lg:max-w-2xl">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>クリック検知閾値</CardTitle>
                <CardDescription>
                  クリックベースの不正検知に使用する閾値を設定します。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                    <Label htmlFor="click_threshold">1日あたりのクリック数上限</Label>
                    <Input id="click_threshold" type="number" defaultValue={50} />
                </div>
                <div className="grid gap-2">
                    <Label htmlFor="media_threshold">重複媒体数上限</Label>
                    <Input id="media_threshold" type="number" defaultValue={3} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>成果検知閾値</CardTitle>
                <CardDescription>
                  成果ベースの不正検知に使用する閾値を設定します。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                    <Label htmlFor="conv_threshold">1日あたりの成果数上限</Label>
                    <Input id="conv_threshold" type="number" defaultValue={5} />
                </div>
                <div className="grid gap-2">
                    <Label htmlFor="conv_media_threshold">重複媒体数上限</Label>
                    <Input id="conv_media_threshold" type="number" defaultValue={2} />
                </div>
              </CardContent>
            </Card>
            
            <div className="flex justify-end">
                <Button>変更を保存</Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

